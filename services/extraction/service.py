"""Extraction service for extracting structured objects from messages."""

import re
from typing import Optional
from uuid import UUID

from shared.contracts import (
    ArtifactRecordedEvent,
    ArtifactType,
    EventType,
    MessageIngestedEvent,
    ObjectExtractedEvent,
    Todo,
    TodoPriority,
    Note,
    Track,
)
from services.event_store.file_store import FileEventStore


class ExtractionService:
    """
    Service for extracting structured objects from messages.
    
    For M0, uses simple keyword detection instead of real LLM.
    M1 will integrate OpenAI API.
    """

    def __init__(self, event_store: FileEventStore):
        self.event_store = event_store

    async def extract_from_message(self, message_event_id: UUID) -> list[UUID]:
        """
        Extract objects from a message event.
        
        Args:
            message_event_id: ID of the MessageIngestedEvent
            
        Returns:
            List of ObjectExtractedEvent IDs
        """
        # Get the message event
        message_event = await self.event_store.get_by_id(message_event_id)
        
        if not message_event or not isinstance(message_event, MessageIngestedEvent):
            return []
        
        content = message_event.content.lower()
        extracted_ids = []
        
        # Simple keyword-based extraction (stub for M0)
        # Todo detection
        if any(keyword in content for keyword in ["todo", "task", "remind me", "need to", "should"]):
            todo = self._extract_todo(message_event.content, message_event_id)
            if todo:
                event_id = await self._record_extracted_object("todo", todo.model_dump(), message_event_id)
                extracted_ids.append(event_id)
        
        # Note detection
        if any(keyword in content for keyword in ["note", "remember", "important", "fyi"]):
            note = self._extract_note(message_event.content, message_event_id)
            if note:
                event_id = await self._record_extracted_object("note", note.model_dump(), message_event_id)
                extracted_ids.append(event_id)
        
        # Track detection
        if any(keyword in content for keyword in ["track", "monitor", "watch", "keep an eye"]):
            track = self._extract_track(message_event.content, message_event_id)
            if track:
                event_id = await self._record_extracted_object("track", track.model_dump(), message_event_id)
                extracted_ids.append(event_id)
        
        return extracted_ids

    def _extract_todo(self, content: str, source_event_id: UUID) -> Optional[Todo]:
        """Extract a todo from content (stub)."""
        # Simple extraction: use first sentence as title
        title = content.split(".")[0].strip()
        if not title:
            title = content[:100]
        
        # Detect priority
        priority = TodoPriority.MEDIUM
        content_lower = content.lower()
        if "urgent" in content_lower or "asap" in content_lower:
            priority = TodoPriority.URGENT
        elif "high priority" in content_lower or "important" in content_lower:
            priority = TodoPriority.HIGH
        elif "low priority" in content_lower or "when you have time" in content_lower:
            priority = TodoPriority.LOW
        
        return Todo(
            title=title,
            description=content if len(content) > len(title) else None,
            priority=priority,
            source_event_id=source_event_id,
        )

    def _extract_note(self, content: str, source_event_id: UUID) -> Optional[Note]:
        """Extract a note from content (stub)."""
        title = content.split(".")[0].strip()
        if not title:
            title = content[:100]
        
        return Note(
            title=title,
            content=content,
            source_event_id=source_event_id,
        )

    def _extract_track(self, content: str, source_event_id: UUID) -> Optional[Track]:
        """Extract a tracking item from content (stub)."""
        title = content.split(".")[0].strip()
        if not title:
            title = content[:100]
        
        return Track(
            title=title,
            description=content,
            source_event_id=source_event_id,
        )

    async def _record_extracted_object(
        self,
        object_type: str,
        object_data: dict,
        source_event_id: UUID,
    ) -> UUID:
        """Record an extracted object as an event."""
        event = ObjectExtractedEvent(
            object_type=object_type,
            object_data=object_data,
            source_event_id=source_event_id,
            extraction_confidence=0.7,  # Stub confidence
        )
        
        return await self.event_store.append(event)
