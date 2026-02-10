"""Interface protocols for service contracts."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from uuid import UUID

from shared.contracts.events import BaseEvent, EventType


class EventStoreProtocol(ABC):
    """Contract for event store operations."""

    @abstractmethod
    async def append(self, event: BaseEvent) -> UUID:
        """
        Append an event to the store.

        Args:
            event: The event to append

        Returns:
            The UUID of the appended event

        Raises:
            EventStoreError: If append fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, event_id: UUID) -> Optional[BaseEvent]:
        """
        Retrieve an event by its ID.

        Args:
            event_id: The UUID of the event

        Returns:
            The event if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_type(
        self,
        event_type: EventType,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> list[BaseEvent]:
        """
        Retrieve events by type and optional time range.

        Args:
            event_type: Type of events to retrieve
            since: Optional start timestamp
            until: Optional end timestamp
            limit: Optional maximum number of events

        Returns:
            List of matching events
        """
        pass

    @abstractmethod
    async def stream_events(
        self,
        since: Optional[datetime] = None,
        event_types: Optional[list[EventType]] = None,
    ) -> list[BaseEvent]:
        """
        Stream events from the log.

        Args:
            since: Optional timestamp to start from
            event_types: Optional filter by event types

        Returns:
            List of events matching criteria
        """
        pass


class ExtractionServiceProtocol(ABC):
    """Contract for extraction service operations."""

    @abstractmethod
    async def extract_objects(self, message: str, context: Optional[dict] = None) -> list[dict]:
        """
        Extract structured objects from a message.

        Args:
            message: The message text to analyze
            context: Optional context for extraction

        Returns:
            List of extracted objects as dicts
        """
        pass


class QueryServiceProtocol(ABC):
    """Contract for query service operations."""

    @abstractmethod
    async def get_todos(
        self,
        status: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        Query todos with optional filters.

        Args:
            status: Optional status filter
            tags: Optional tag filters

        Returns:
            List of matching todos
        """
        pass

    @abstractmethod
    async def get_notes(
        self,
        tags: Optional[list[str]] = None,
        search: Optional[str] = None,
    ) -> list[dict]:
        """
        Query notes with optional filters.

        Args:
            tags: Optional tag filters
            search: Optional text search

        Returns:
            List of matching notes
        """
        pass

    @abstractmethod
    async def get_tracks(
        self,
        status: Optional[str] = None,
    ) -> list[dict]:
        """
        Query tracking items with optional filters.

        Args:
            status: Optional status filter

        Returns:
            List of matching tracks
        """
        pass
