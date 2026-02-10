"""File-based event store implementation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

from shared.contracts import BaseEvent, EventType


class FileEventStore:
    """
    File-based append-only event store using JSONL format.
    
    Each event is a JSON object on a single line.
    Files are organized by date for manageability.
    """

    def __init__(self, data_dir: str = "./data/events"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_current_file(self) -> Path:
        """Get the current event log file path."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return self.data_dir / f"events-{today}.jsonl"

    async def append(self, event: BaseEvent) -> UUID:
        """
        Append an event to the store.
        
        Args:
            event: The event to append
            
        Returns:
            The UUID of the appended event
        """
        event_file = self._get_current_file()
        
        # Serialize event to JSON
        event_json = event.model_dump_json()
        
        # Append to file (atomic within line)
        with open(event_file, "a") as f:
            f.write(event_json + "\n")
        
        return event.event_id

    async def get_by_id(self, event_id: UUID) -> Optional[BaseEvent]:
        """
        Retrieve an event by its ID.
        
        Args:
            event_id: The UUID of the event
            
        Returns:
            The event if found, None otherwise
        """
        # Search all event files (inefficient but acceptable for M0)
        for event_file in sorted(self.data_dir.glob("events-*.jsonl")):
            with open(event_file, "r") as f:
                for line in f:
                    try:
                        event_data = json.loads(line)
                        if event_data.get("event_id") == str(event_id):
                            # Reconstruct event object
                            return self._deserialize_event(event_data)
                    except json.JSONDecodeError:
                        continue
        
        return None

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
        events = []
        count = 0
        
        for event_file in sorted(self.data_dir.glob("events-*.jsonl")):
            with open(event_file, "r") as f:
                for line in f:
                    try:
                        event_data = json.loads(line)
                        
                        # Filter by type
                        if event_data.get("event_type") != event_type.value:
                            continue
                        
                        # Filter by time range
                        event_time = datetime.fromisoformat(
                            event_data["timestamp"].replace("Z", "+00:00")
                        )
                        if since and event_time < since:
                            continue
                        if until and event_time > until:
                            continue
                        
                        events.append(self._deserialize_event(event_data))
                        count += 1
                        
                        if limit and count >= limit:
                            return events
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        return events

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
        events = []
        
        for event_file in sorted(self.data_dir.glob("events-*.jsonl")):
            with open(event_file, "r") as f:
                for line in f:
                    try:
                        event_data = json.loads(line)
                        
                        # Filter by time
                        if since:
                            event_time = datetime.fromisoformat(
                                event_data["timestamp"].replace("Z", "+00:00")
                            )
                            if event_time < since:
                                continue
                        
                        # Filter by type
                        if event_types:
                            event_type_values = [et.value for et in event_types]
                            if event_data.get("event_type") not in event_type_values:
                                continue
                        
                        events.append(self._deserialize_event(event_data))
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        return events

    def _deserialize_event(self, event_data: dict) -> BaseEvent:
        """Deserialize event data back to event object."""
        from shared.contracts import (
            ArtifactRecordedEvent,
            MessageIngestedEvent,
            ObjectExtractedEvent,
        )
        
        event_type = event_data.get("event_type")
        
        # Map to appropriate event class
        if event_type == EventType.MESSAGE_INGESTED.value:
            return MessageIngestedEvent(**event_data)
        elif event_type == EventType.ARTIFACT_RECORDED.value:
            return ArtifactRecordedEvent(**event_data)
        elif event_type == EventType.OBJECT_EXTRACTED.value:
            return ObjectExtractedEvent(**event_data)
        else:
            # Fall back to base event
            return BaseEvent(**event_data)
