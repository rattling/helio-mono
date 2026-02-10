"""Query service for building projections and querying objects."""

from typing import Optional

from shared.contracts import EventType, ObjectExtractedEvent, Todo, Note, Track
from services.event_store.file_store import FileEventStore


class QueryService:
    """
    Service for building queryable projections from the event log.
    
    For M0, uses in-memory projections.
    M1 will use SQLite for persistence.
    """

    def __init__(self, event_store: FileEventStore):
        self.event_store = event_store
        self._todos: dict = {}
        self._notes: dict = {}
        self._tracks: dict = {}

    async def rebuild_projections(self):
        """Rebuild all projections from the event log."""
        self._todos.clear()
        self._notes.clear()
        self._tracks.clear()
        
        # Stream all object extraction events
        events = await self.event_store.stream_events(
            event_types=[EventType.OBJECT_EXTRACTED]
        )
        
        for event in events:
            if isinstance(event, ObjectExtractedEvent):
                await self._apply_extraction_event(event)

    async def _apply_extraction_event(self, event: ObjectExtractedEvent):
        """Apply an extraction event to projections."""
        if event.object_type == "todo":
            todo = Todo(**event.object_data)
            self._todos[str(todo.object_id)] = todo
        elif event.object_type == "note":
            note = Note(**event.object_data)
            self._notes[str(note.object_id)] = note
        elif event.object_type == "track":
            track = Track(**event.object_data)
            self._tracks[str(track.object_id)] = track

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
        todos = list(self._todos.values())
        
        # Filter by status
        if status:
            todos = [t for t in todos if t.status.value == status]
        
        # Filter by tags
        if tags:
            todos = [t for t in todos if any(tag in t.tags for tag in tags)]
        
        return [t.model_dump() for t in todos]

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
        notes = list(self._notes.values())
        
        # Filter by tags
        if tags:
            notes = [n for n in notes if any(tag in n.tags for tag in tags)]
        
        # Filter by search
        if search:
            search_lower = search.lower()
            notes = [
                n for n in notes
                if search_lower in n.title.lower() or search_lower in n.content.lower()
            ]
        
        return [n.model_dump() for n in notes]

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
        tracks = list(self._tracks.values())
        
        # Filter by status
        if status:
            tracks = [t for t in tracks if t.status.value == status]
        
        return [t.model_dump() for t in tracks]

    def get_stats(self) -> dict:
        """Get statistics about current projections."""
        return {
            "todos": len(self._todos),
            "notes": len(self._notes),
            "tracks": len(self._tracks),
            "total_objects": len(self._todos) + len(self._notes) + len(self._tracks),
        }
