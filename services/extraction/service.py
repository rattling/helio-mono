"""Extraction service for extracting structured objects from messages."""

import logging
from typing import Optional
from uuid import UUID

from shared.contracts import (
    EventType,
    MessageIngestedEvent,
    ObjectExtractedEvent,
    Todo,
    Note,
    Track,
)
from shared.contracts.protocols import LLMServiceProtocol, EventStoreProtocol

logger = logging.getLogger(__name__)


class ExtractionService:
    """
    Service for extracting structured objects from messages using LLM.

    Delegates actual extraction to LLMServiceProtocol implementation
    (OpenAI or Mock), manages object validation and event recording.
    """

    def __init__(self, event_store: EventStoreProtocol, llm_service: LLMServiceProtocol):
        """
        Initialize extraction service.

        Args:
            event_store: Event store for reading messages and recording objects
            llm_service: LLM service for extraction (OpenAI or Mock)
        """
        self.event_store = event_store
        self.llm_service = llm_service

    async def extract_from_message(
        self, message_event_id: UUID, context: Optional[dict] = None
    ) -> list[tuple[UUID, str, dict]]:
        """
        Extract objects from a message event using LLM.

        Args:
            message_event_id: ID of the MessageIngestedEvent
            context: Optional context for extraction (conversation history, etc.)

        Returns:
            List of tuples (event_id, object_type, object_data) for extracted objects
        """
        # Get the message event
        message_event = await self.event_store.get_by_id(message_event_id)

        if not message_event or not isinstance(message_event, MessageIngestedEvent):
            logger.warning(f"Message event {message_event_id} not found or invalid type")
            return []

        # Extract using LLM
        try:
            result = await self.llm_service.extract_objects(message_event.content, context=context)
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return []

        logger.info(
            f"Extracted {len(result.objects)} objects from message {message_event_id} "
            f"(model: {result.model_used}, tokens: {result.tokens_used})"
        )

        # Validate and record each extracted object
        extracted_items = []
        for obj_data in result.objects:
            try:
                # Validate object type and schema
                validated_obj = self._validate_object(obj_data, message_event_id)
                if validated_obj:
                    event_id = await self._record_extracted_object(
                        object_type=obj_data["type"],
                        object_data=validated_obj.model_dump(),
                        source_event_id=message_event_id,
                        confidence=result.confidence,
                        extraction_metadata={
                            **result.extraction_metadata,
                            "prompt_artifact_id": str(result.prompt_artifact_id),
                            "response_artifact_id": str(result.response_artifact_id),
                        },
                    )
                    extracted_items.append((event_id, obj_data["type"], validated_obj.model_dump()))
            except Exception as e:
                logger.warning(f"Failed to validate/record object {obj_data}: {e}")
                continue

        return extracted_items

    def _validate_object(
        self, obj_data: dict, source_event_id: UUID
    ) -> Optional[Todo | Note | Track]:
        """
        Validate and construct typed object from extraction data.

        Args:
            obj_data: Raw object dict from LLM
            source_event_id: Source message event ID

        Returns:
            Validated Pydantic model or None if invalid
        """
        obj_type = obj_data.get("type")

        try:
            if obj_type == "todo":
                return Todo(
                    title=obj_data["title"],
                    description=obj_data.get("description"),
                    priority=obj_data.get("priority", "medium"),
                    due_date=obj_data.get("due_date"),
                    tags=obj_data.get("tags", []),
                    source_event_id=source_event_id,
                )

            elif obj_type == "note":
                return Note(
                    title=obj_data["title"],
                    content=obj_data.get("content", obj_data["title"]),
                    tags=obj_data.get("tags", []),
                    source_event_id=source_event_id,
                )

            elif obj_type == "track":
                return Track(
                    title=obj_data["title"],
                    description=obj_data.get("description"),
                    check_in_frequency=obj_data.get("check_in_frequency"),
                    tags=obj_data.get("tags", []),
                    source_event_id=source_event_id,
                )

            else:
                logger.warning(f"Unknown object type: {obj_type}")
                return None

        except Exception as e:
            logger.warning(f"Object validation failed: {e}")
            return None

    async def _record_extracted_object(
        self,
        object_type: str,
        object_data: dict,
        source_event_id: UUID,
        confidence: float,
        extraction_metadata: dict,
    ) -> UUID:
        """
        Record an extracted object as an event.

        Args:
            object_type: Type of object (todo, note, track)
            object_data: Validated object data
            source_event_id: Source message event ID
            confidence: Extraction confidence (0-1)
            extraction_metadata: LLM extraction metadata

        Returns:
            UUID of the ObjectExtractedEvent
        """
        event = ObjectExtractedEvent(
            object_type=object_type,
            object_data=object_data,
            source_event_id=source_event_id,
            extraction_confidence=confidence,
            extraction_metadata=extraction_metadata,
        )

        event_id = await self.event_store.append(event)
        logger.debug(f"Recorded {object_type} object: {event_id}")
        return event_id
