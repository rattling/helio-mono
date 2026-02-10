"""Ingestion service for normalizing and recording inputs."""

from typing import Optional
from uuid import UUID

from shared.contracts import MessageIngestedEvent, SourceType
from services.event_store.file_store import FileEventStore


class IngestionService:
    """Service for ingesting messages from various sources."""

    def __init__(self, event_store: FileEventStore):
        self.event_store = event_store

    async def ingest_message(
        self,
        content: str,
        source: SourceType,
        source_id: str,
        author: Optional[str] = None,
        conversation_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> UUID:
        """
        Ingest a message from any source.
        
        Args:
            content: The message content
            source: Source type (ChatGPT, Telegram, CLI)
            source_id: Original ID from source system
            author: Optional author (user or assistant)
            conversation_id: Optional conversation grouping ID
            metadata: Optional additional metadata
            
        Returns:
            Event ID of the ingested message event
        """
        event = MessageIngestedEvent(
            source=source,
            source_id=source_id,
            content=content,
            author=author,
            conversation_id=conversation_id,
            metadata=metadata or {},
        )
        
        event_id = await self.event_store.append(event)
        return event_id
