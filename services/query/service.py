"""Query service for building projections and querying objects."""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime

from shared.contracts import EventType, ObjectExtractedEvent, Todo, Note, Track
from services.event_store.file_store import FileEventStore
from .database import (
    initialize_database,
    create_connection,
    check_schema_version,
    execute_with_retry,
    transaction,
)

logger = logging.getLogger(__name__)


class QueryService:
    """
    Service for building queryable projections from the event log.
    
    For M1, uses SQLite for durable persistence.
    """

    def __init__(self, event_store: FileEventStore, db_path: Optional[Path] = None):
        self.event_store = event_store
        
        # Default database path
        if db_path is None:
            db_path = Path("./data/projections/helionyx.db")
        
        self.db_path = Path(db_path)
        
        # Initialize database if needed
        initialize_database(self.db_path)
        
        # Create persistent connection
        self.conn = create_connection(self.db_path)
        
        # Verify schema version
        check_schema_version(self.conn, expected=1)
        
        logger.info(f"Query service initialized with database: {self.db_path}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    async def rebuild_projections(self):
        """Rebuild all projections from the event log."""
        logger.info("Starting projection rebuild...")
        
        with transaction(self.conn):
            # 1. Clear all projection tables
            self.conn.execute("DELETE FROM todos")
            self.conn.execute("DELETE FROM notes")
            self.conn.execute("DELETE FROM tracks")
            
            logger.info("Cleared existing projections")
            
            # 2. Stream all object extraction events
            events = await self.event_store.stream_events(
                event_types=[EventType.OBJECT_EXTRACTED]
            )
            
            logger.info(f"Processing {len(events)} extraction events...")
            
            # 3. Apply each event to appropriate table
            for event in events:
                if isinstance(event, ObjectExtractedEvent):
                    await self._apply_extraction_event(event)
            
            # 4. Update metadata
            now = datetime.utcnow().isoformat()
            self.conn.execute(
                "INSERT OR REPLACE INTO projection_metadata (key, value, updated_at) "
                "VALUES (?, ?, ?)",
                ("last_rebuild_timestamp", now, now)
            )
            
            if events:
                last_event_id = str(events[-1].event_id)
                self.conn.execute(
                    "INSERT OR REPLACE INTO projection_metadata (key, value, updated_at) "
                    "VALUES (?, ?, ?)",
                    ("last_event_id_processed", last_event_id, now)
                )
        
        logger.info("Projection rebuild complete")

    async def _apply_extraction_event(self, event: ObjectExtractedEvent):
        """Apply an extraction event to projections."""
        if event.object_type == "todo":
            await self._upsert_todo(event.object_data)
        elif event.object_type == "note":
            await self._upsert_note(event.object_data)
        elif event.object_type == "track":
            await self._upsert_track(event.object_data)

    async def _upsert_todo(self, data: dict):
        """Insert or update a todo in the database."""
        # Parse Todo object
        todo = Todo(**data)
        
        # Convert to database format
        tags_json = json.dumps(todo.tags) if todo.tags else None
        due_date = todo.due_date.isoformat() if todo.due_date else None
        completed_at = todo.completed_at.isoformat() if todo.completed_at else None
        
        await execute_with_retry(
            self.conn,
            """
            INSERT OR REPLACE INTO todos (
                object_id, title, description, status, priority,
                due_date, created_at, completed_at, tags,
                source_event_id, last_updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(todo.object_id),
                todo.title,
                todo.description,
                todo.status.value,
                todo.priority.value,
                due_date,
                todo.created_at.isoformat(),
                completed_at,
                tags_json,
                str(todo.source_event_id),
                datetime.utcnow().isoformat(),
            )
        )

    async def _upsert_note(self, data: dict):
        """Insert or update a note in the database."""
        # Parse Note object
        note = Note(**data)
        
        # Convert to database format
        tags_json = json.dumps(note.tags) if note.tags else None
        
        await execute_with_retry(
            self.conn,
            """
            INSERT OR REPLACE INTO notes (
                object_id, title, content, created_at, tags,
                source_event_id, last_updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(note.object_id),
                note.title,
                note.content,
                note.created_at.isoformat(),
                tags_json,
                str(note.source_event_id),
                datetime.utcnow().isoformat(),
            )
        )

    async def _upsert_track(self, data: dict):
        """Insert or update a track in the database."""
        # Parse Track object
        track = Track(**data)
        
        # Convert to database format
        tags_json = json.dumps(track.tags) if track.tags else None
        last_updated = track.last_updated.isoformat() if track.last_updated else None
        
        await execute_with_retry(
            self.conn,
            """
            INSERT OR REPLACE INTO tracks (
                object_id, title, description, status, created_at,
                last_updated, tags, source_event_id, check_in_frequency,
                projection_updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(track.object_id),
                track.title,
                track.description,
                track.status.value,
                track.created_at.isoformat(),
                last_updated,
                tags_json,
                str(track.source_event_id),
                track.check_in_frequency,
                datetime.utcnow().isoformat(),
            )
        )

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
        query = "SELECT * FROM todos WHERE 1=1"
        params = []
        
        # Filter by status
        if status:
            query += " AND status = ?"
            params.append(status)
        
        # Filter by tags (simple substring match in JSON)
        if tags:
            for tag in tags:
                query += " AND tags LIKE ?"
                params.append(f'%"{tag}"%')
        
        query += " ORDER BY created_at DESC"
        
        cursor = await execute_with_retry(self.conn, query, tuple(params))
        rows = cursor.fetchall()
        
        # Convert Row objects to dicts
        return [dict(row) for row in rows]

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
        query = "SELECT * FROM notes WHERE 1=1"
        params = []
        
        # Text search
        if search:
            query += " AND (title LIKE ? OR content LIKE ?)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])
        
        # Filter by tags
        if tags:
            for tag in tags:
                query += " AND tags LIKE ?"
                params.append(f'%"{tag}"%')
        
        query += " ORDER BY created_at DESC"
        
        cursor = await execute_with_retry(self.conn, query, tuple(params))
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]

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
        query = "SELECT * FROM tracks WHERE 1=1"
        params = []
        
        # Filter by status
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        cursor = await execute_with_retry(self.conn, query, tuple(params))
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]

    def get_stats(self) -> dict:
        """Get statistics about current projections."""
        cursor = self.conn.execute(
            "SELECT 'todos', COUNT(*) FROM todos "
            "UNION ALL SELECT 'notes', COUNT(*) FROM notes "
            "UNION ALL SELECT 'tracks', COUNT(*) FROM tracks"
        )
        
        rows = cursor.fetchall()
        stats = {row[0]: row[1] for row in rows}
        stats["total_objects"] = sum(stats.values())
        
        # Get last rebuild time
        cursor = self.conn.execute(
            "SELECT value FROM projection_metadata WHERE key = ?",
            ("last_rebuild_timestamp",)
        )
        row = cursor.fetchone()
        if row and row[0]:
            stats["last_rebuild"] = row[0]
        else:
            stats["last_rebuild"] = "Never"
        
        # Get event count (approximate - from event store)
        # This would need event_store integration, stubbed for now
        stats["total_events"] = "N/A"
        
        return stats
