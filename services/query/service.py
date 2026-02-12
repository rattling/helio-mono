"""Query service for building projections and querying objects."""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

from shared.contracts import (
    EventType,
    ObjectExtractedEvent,
    DecisionRecordedEvent,
    Todo,
    Note,
    Track,
    Task,
    TaskStatus,
    SourceType,
    TASK_LABEL_NEEDS_REVIEW,
)
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
            self.conn.execute("DELETE FROM tasks")

            logger.info("Cleared existing projections")

            # 2. Stream all events relevant to projections
            events = await self.event_store.stream_events(
                event_types=[EventType.OBJECT_EXTRACTED, EventType.DECISION_RECORDED]
            )

            logger.info(f"Processing {len(events)} extraction events...")

            # 3. Apply each event to appropriate table
            todo_ordinals: dict[str, int] = {}
            for event in events:
                if isinstance(event, ObjectExtractedEvent):
                    await self._apply_extraction_event(event, todo_ordinals)
                elif isinstance(event, DecisionRecordedEvent):
                    await self._apply_decision_event(event)

            # 4. Update metadata
            now = datetime.utcnow().isoformat()
            self.conn.execute(
                "INSERT OR REPLACE INTO projection_metadata (key, value, updated_at) "
                "VALUES (?, ?, ?)",
                ("last_rebuild_timestamp", now, now),
            )

            if events:
                last_event_id = str(events[-1].event_id)
                self.conn.execute(
                    "INSERT OR REPLACE INTO projection_metadata (key, value, updated_at) "
                    "VALUES (?, ?, ?)",
                    ("last_event_id_processed", last_event_id, now),
                )

        logger.info("Projection rebuild complete")

    async def _apply_extraction_event(
        self,
        event: ObjectExtractedEvent,
        todo_ordinals: Optional[dict[str, int]] = None,
    ):
        """Apply an extraction event to projections."""
        if event.object_type == "todo":
            await self._upsert_todo(event.object_data)
            source_key = str(event.source_event_id)
            ordinal = 0
            if todo_ordinals is not None:
                ordinal = todo_ordinals.get(source_key, 0)
                todo_ordinals[source_key] = ordinal + 1
            await self._canonicalize_todo_to_task(event, ordinal)
        elif event.object_type == "note":
            await self._upsert_note(event.object_data)
        elif event.object_type == "track":
            await self._upsert_track(event.object_data)

    async def _apply_decision_event(self, event: DecisionRecordedEvent):
        """Apply decision events that carry task snapshots."""
        decision_data = event.decision_data or {}
        if decision_data.get("domain") != "task":
            return

        task_snapshot = decision_data.get("task_snapshot")
        if not isinstance(task_snapshot, dict):
            return

        await self._upsert_task(task_snapshot)

    async def _canonicalize_todo_to_task(self, event: ObjectExtractedEvent, ordinal: int):
        """Bridge extracted todos into canonical Task projections."""
        todo_data = event.object_data
        title = todo_data.get("title")
        if not title:
            return

        source_ref = f"message_event:{event.source_event_id}:todo:{ordinal}"
        existing = self.conn.execute(
            "SELECT task_id FROM tasks WHERE source = ? AND source_ref = ?",
            (SourceType.API.value, source_ref),
        ).fetchone()
        if existing:
            return

        now = datetime.utcnow()
        task = Task(
            title=title,
            body=todo_data.get("description"),
            source=SourceType.API,
            source_ref=source_ref,
            due_at=todo_data.get("due_date"),
            labels=[TASK_LABEL_NEEDS_REVIEW],
            created_at=now,
            updated_at=now,
            explanations=[],
        )
        await self._upsert_task(task.model_dump(mode="json"))

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
            ),
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
            ),
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
            ),
        )

    async def _upsert_task(self, data: dict):
        """Insert or update a task in the database."""
        task = Task(**data)

        labels_json = json.dumps(task.labels) if task.labels else "[]"
        blocked_by_json = json.dumps([str(item) for item in task.blocked_by])
        explanations_json = json.dumps([item.model_dump(mode="json") for item in task.explanations])

        await execute_with_retry(
            self.conn,
            """
            INSERT OR REPLACE INTO tasks (
                task_id, title, body, status, priority,
                due_at, do_not_start_before, created_at, updated_at,
                completed_at, source, source_ref, dedup_group_id,
                labels, project, blocked_by, agent_notes, explanations
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(task.task_id),
                task.title,
                task.body,
                task.status.value,
                task.priority.value,
                task.due_at.isoformat() if task.due_at else None,
                task.do_not_start_before.isoformat() if task.do_not_start_before else None,
                task.created_at.isoformat(),
                task.updated_at.isoformat(),
                task.completed_at.isoformat() if task.completed_at else None,
                task.source.value,
                task.source_ref,
                task.dedup_group_id,
                labels_json,
                task.project,
                blocked_by_json,
                task.agent_notes,
                explanations_json,
            ),
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

    async def get_tasks(self, status: Optional[str] = None) -> list[dict]:
        """Query tasks with optional status filter."""
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY updated_at DESC"

        cursor = await execute_with_retry(self.conn, query, tuple(params))
        rows = cursor.fetchall()
        return [self._deserialize_task_row(dict(row)) for row in rows]

    async def get_task_by_id(self, task_id: str) -> Optional[dict]:
        """Get a single task by id."""
        cursor = await execute_with_retry(
            self.conn,
            "SELECT * FROM tasks WHERE task_id = ?",
            (task_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self._deserialize_task_row(dict(row))

    async def get_review_queue(self, limit: int = 50) -> list[dict]:
        """Get deterministically ordered review queue with passive stale detection."""
        cursor = await execute_with_retry(
            self.conn,
            "SELECT * FROM tasks WHERE status NOT IN (?, ?) ORDER BY updated_at ASC",
            (TaskStatus.DONE.value, TaskStatus.CANCELLED.value),
        )
        rows = [self._deserialize_task_row(dict(row)) for row in cursor.fetchall()]

        def priority_rank(priority: str) -> int:
            return {"p0": 0, "p1": 1, "p2": 2, "p3": 3}.get(priority, 99)

        def updated_at_value(task: dict) -> str:
            return task.get("updated_at") or ""

        def sort_key(task: dict):
            labels = task.get("labels") or []
            needs_review = TASK_LABEL_NEEDS_REVIEW in labels
            stale = self._is_task_stale(task)
            return (
                0 if needs_review else 1,
                0 if stale else 1,
                priority_rank(task.get("priority", "p3")),
                updated_at_value(task),
            )

        ordered = sorted(rows, key=sort_key)
        for task in ordered:
            task["is_stale"] = self._is_task_stale(task)

        return ordered[:limit]

    def _is_task_stale(self, task: dict) -> bool:
        """Passive stale detection for review queue."""
        status = task.get("status")
        if status in (TaskStatus.DONE.value, TaskStatus.CANCELLED.value):
            return False

        now = datetime.utcnow()
        due_at = self._parse_iso(task.get("due_at"))
        if due_at and due_at < now:
            return True

        updated_at = self._parse_iso(task.get("updated_at"))
        if updated_at and updated_at < now - timedelta(days=7):
            return True

        return False

    def _parse_iso(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None

    def _deserialize_task_row(self, row: dict) -> dict:
        row["labels"] = json.loads(row.get("labels") or "[]")
        row["blocked_by"] = json.loads(row.get("blocked_by") or "[]")
        row["explanations"] = json.loads(row.get("explanations") or "[]")
        return row

    def get_stats(self) -> dict:
        """Get statistics about current projections."""
        cursor = self.conn.execute(
            "SELECT 'todos', COUNT(*) FROM todos "
            "UNION ALL SELECT 'notes', COUNT(*) FROM notes "
            "UNION ALL SELECT 'tracks', COUNT(*) FROM tracks "
            "UNION ALL SELECT 'tasks', COUNT(*) FROM tasks"
        )

        rows = cursor.fetchall()
        stats = {row[0]: row[1] for row in rows}
        stats["total_objects"] = (
            stats.get("todos", 0) + stats.get("notes", 0) + stats.get("tracks", 0)
        )

        # Get last rebuild time
        cursor = self.conn.execute(
            "SELECT value FROM projection_metadata WHERE key = ?", ("last_rebuild_timestamp",)
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
