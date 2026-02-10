"""Mock LLM service for testing without real API calls."""

import json
import logging
from typing import Optional
from uuid import uuid4

from shared.contracts.objects import ExtractionResult
from shared.contracts.protocols import LLMServiceProtocol, EventStoreProtocol
from shared.contracts.events import ArtifactRecordedEvent, ArtifactType
from services.extraction.prompts import build_prompts

logger = logging.getLogger(__name__)


class MockLLMService(LLMServiceProtocol):
    """
    Predictable LLM for testing.
    
    Uses simple keyword detection to simulate extraction without API calls.
    """

    def __init__(
        self,
        event_store: EventStoreProtocol,
        responses: Optional[dict] = None,
    ):
        """
        Initialize mock LLM service.
        
        Args:
            event_store: Event store for recording artifacts
            responses: Optional dict mapping message patterns to responses
        """
        self.event_store = event_store
        self.responses = responses or {}
        self.call_count = 0

    async def extract_objects(
        self,
        message: str,
        context: Optional[dict] = None
    ) -> ExtractionResult:
        """
        Extract objects using keyword-based detection.
        
        Args:
            message: Message text to analyze
            context: Optional context (ignored in mock)
            
        Returns:
            ExtractionResult with mock extracted objects
        """
        self.call_count += 1
        
        system_prompt, user_prompt = build_prompts(message, context)
        
        # Record prompt artifact
        prompt_artifact_id = await self._record_artifact(
            artifact_type=ArtifactType.LLM_PROMPT,
            content=json.dumps({"system": system_prompt, "user": user_prompt}),
            metadata={"model": "mock-llm", "mock": True}
        )
        
        # Check for custom responses
        for pattern, response in self.responses.items():
            if pattern.lower() in message.lower():
                objects = response if isinstance(response, list) else [response]
                return await self._create_result(
                    objects,
                    prompt_artifact_id,
                    tokens=len(message.split()) * 2
                )
        
        # Default keyword-based extraction
        objects = []
        message_lower = message.lower()
        
        # Todo detection
        if any(kw in message_lower for kw in ["todo", "task", "remind me", "need to", "should"]):
            title = message.split(".")[0].strip() if "." in message else message[:100]
            priority = "medium"
            
            if "urgent" in message_lower or "asap" in message_lower:
                priority = "urgent"
            elif "important" in message_lower or "high priority" in message_lower:
                priority = "high"
            elif "low priority" in message_lower or "when you have time" in message_lower:
                priority = "low"
            
            objects.append({
                "type": "todo",
                "title": title,
                "description": message if len(message) > len(title) else None,
                "priority": priority,
                "due_date": None,
                "tags": []
            })
        
        # Note detection
        if any(kw in message_lower for kw in ["note", "remember", "important", "fyi"]):
            title = message.split(".")[0].strip() if "." in message else message[:100]
            objects.append({
                "type": "note",
                "title": title,
                "content": message,
                "tags": []
            })
        
        # Track detection
        if any(kw in message_lower for kw in ["track", "monitor", "watch", "keep an eye"]):
            title = message.split(".")[0].strip() if "." in message else message[:100]
            objects.append({
                "type": "track",
                "title": title,
                "description": message,
                "check_in_frequency": None,
                "tags": []
            })
        
        return await self._create_result(
            objects,
            prompt_artifact_id,
            tokens=len(message.split()) * 2
        )

    async def _create_result(
        self,
        objects: list[dict],
        prompt_artifact_id: uuid4,
        tokens: int
    ) -> ExtractionResult:
        """
        Create an ExtractionResult with mock metadata.
        
        Args:
            objects: Extracted objects
            prompt_artifact_id: UUID of prompt artifact
            tokens: Mock token count
            
        Returns:
            ExtractionResult
        """
        # Record mock response artifact
        response_artifact_id = await self._record_artifact(
            artifact_type=ArtifactType.LLM_RESPONSE,
            content=json.dumps({"objects": objects, "mock": True}),
            metadata={
                "model": "mock-llm",
                "tokens": tokens,
                "mock": True
            }
        )
        
        logger.info(f"Mock LLM extraction: {len(objects)} objects, {tokens} mock tokens")
        
        return ExtractionResult(
            objects=objects,
            confidence=0.95 if objects else 0.0,
            model_used="mock-llm",
            tokens_used=tokens,
            prompt_artifact_id=prompt_artifact_id,
            response_artifact_id=response_artifact_id,
            extraction_metadata={
                "mock": True,
                "call_count": self.call_count
            }
        )

    async def _record_artifact(
        self,
        artifact_type: ArtifactType,
        content: str,
        metadata: dict
    ) -> uuid4:
        """
        Record an artifact in the event store.
        
        Args:
            artifact_type: Type of artifact (prompt or response)
            content: Artifact content
            metadata: Artifact metadata
            
        Returns:
            UUID of the recorded artifact event
        """
        event = ArtifactRecordedEvent(
            artifact_type=artifact_type,
            content=content,
            metadata=metadata
        )
        return await self.event_store.append(event)
