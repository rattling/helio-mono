"""Tests for SQLite query service."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from uuid import uuid4

from services.query.service import QueryService
from services.query.database import initialize_database, get_schema_version
from services.event_store.file_store import FileEventStore
from shared.contracts import (
    ObjectExtractedEvent,
    Todo,
    TodoStatus,
    TodoPriority,
    Note,
    Track,
    TrackStatus,
)


@pytest.fixture
def temp_db():
    """Create temporary SQLite database for tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    yield db_path
    
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def temp_event_store():
    """Create temporary event store for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FileEventStore(data_dir=tmpdir)
        yield store


@pytest.mark.asyncio
async def test_database_initialization(temp_db):
    """Test database is initialized with correct schema."""
    initialize_database(temp_db)
    
    assert temp_db.exists()
    
    # Check schema version
    import sqlite3
    conn = sqlite3.connect(temp_db)
    version = get_schema_version(conn)
    assert version == 1
    
    # Check tables exist
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    tables = {row[0] for row in cursor.fetchall()}
    
    assert 'todos' in tables
    assert 'notes' in tables
    assert 'tracks' in tables
    assert 'projection_metadata' in tables
    
    conn.close()


@pytest.mark.asyncio
async def test_query_service_initialization(temp_db, temp_event_store):
    """Test query service initializes correctly."""
    service = QueryService(temp_event_store, db_path=temp_db)
    
    assert service.conn is not None
    assert service.db_path == temp_db
    
    service.close()


@pytest.mark.asyncio
async def test_rebuild_empty_projections(temp_db, temp_event_store):
    """Test rebuilding projections with no events."""
    service = QueryService(temp_event_store, db_path=temp_db)
    
    await service.rebuild_projections()
    
    stats = service.get_stats()
    assert stats['todos'] == 0
    assert stats['notes'] == 0
    assert stats['tracks'] == 0
    assert stats['total_objects'] == 0
    assert stats['last_rebuild'] != "Never"
    
    service.close()


@pytest.mark.asyncio
async def test_rebuild_with_todos(temp_db, temp_event_store):
    """Test rebuilding projections with todo events."""
    # Create todo object
    todo = Todo(
        title="Test todo",
        description="Test description",
        priority=TodoPriority.HIGH,
        status=TodoStatus.PENDING,
        source_event_id=uuid4(),
    )
    
    # Create extraction event
    event = ObjectExtractedEvent(
        object_type="todo",
        object_data=todo.model_dump(),
        confidence=0.95,
        source_event_id=uuid4(),
    )
    
    # Append to event store
    await temp_event_store.append(event)
    
    # Rebuild projections
    service = QueryService(temp_event_store, db_path=temp_db)
    await service.rebuild_projections()
    
    # Query todos
    todos = await service.get_todos()
    
    assert len(todos) == 1
    assert todos[0]['title'] == "Test todo"
    assert todos[0]['priority'] == 'high'
    assert todos[0]['status'] == 'pending'
    
    service.close()


@pytest.mark.asyncio
async def test_get_todos_with_filters(temp_db, temp_event_store):
    """Test querying todos with filters."""
    # Create multiple todos
    todo1 = Todo(
        title="Urgent task",
        priority=TodoPriority.URGENT,
        status=TodoStatus.PENDING,
        source_event_id=uuid4(),
    )
    
    todo2 = Todo(
        title="Completed task",
        priority=TodoPriority.LOW,
        status=TodoStatus.COMPLETED,
        source_event_id=uuid4(),
    )
    
    # Create events
    for todo in [todo1, todo2]:
        event = ObjectExtractedEvent(
            object_type="todo",
            object_data=todo.model_dump(),
            confidence=0.95,
            source_event_id=uuid4(),
        )
        await temp_event_store.append(event)
    
    # Rebuild and query
    service = QueryService(temp_event_store, db_path=temp_db)
    await service.rebuild_projections()
    
    # Filter by status
    pending = await service.get_todos(status="pending")
    assert len(pending) == 1
    assert pending[0]['title'] == "Urgent task"
    
    completed = await service.get_todos(status="completed")
    assert len(completed) == 1
    assert completed[0]['title'] == "Completed task"
    
    service.close()


@pytest.mark.asyncio
async def test_get_notes_with_search(temp_db, temp_event_store):
    """Test querying notes with text search."""
    # Create notes
    note1 = Note(
        title="Meeting notes",
        content="Discussed project timeline",
        source_event_id=uuid4(),
    )
    
    note2 = Note(
        title="Research",
        content="LLM integration patterns",
        source_event_id=uuid4(),
    )
    
    # Create events
    for note in [note1, note2]:
        event = ObjectExtractedEvent(
            object_type="note",
            object_data=note.model_dump(),
            confidence=0.95,
            source_event_id=uuid4(),
        )
        await temp_event_store.append(event)
    
    # Rebuild and query
    service = QueryService(temp_event_store, db_path=temp_db)
    await service.rebuild_projections()
    
    # Search in content
    results = await service.get_notes(search="timeline")
    assert len(results) == 1
    assert results[0]['title'] == "Meeting notes"
    
    # Search in title
    results = await service.get_notes(search="Research")
    assert len(results) == 1
    assert results[0]['title'] == "Research"
    
    # No match
    results = await service.get_notes(search="nonexistent")
    assert len(results) == 0
    
    service.close()


@pytest.mark.asyncio
async def test_stats_after_rebuild(temp_db, temp_event_store):
    """Test stats are correct after rebuilding."""
    # Create mixed objects
    todo = Todo(title="Test", source_event_id=uuid4())
    note = Note(title="Note", content="Content", source_event_id=uuid4())
    track = Track(title="Track", source_event_id=uuid4())
    
    for obj_type, obj_data in [
        ("todo", todo.model_dump()),
        ("note", note.model_dump()),
        ("track", track.model_dump()),
    ]:
        event = ObjectExtractedEvent(
            object_type=obj_type,
            object_data=obj_data,
            confidence=0.95,
            source_event_id=uuid4(),
        )
        await temp_event_store.append(event)
    
    # Rebuild and check stats
    service = QueryService(temp_event_store, db_path=temp_db)
    await service.rebuild_projections()
    
    stats = service.get_stats()
    
    assert stats['todos'] == 1
    assert stats['notes'] == 1
    assert stats['tracks'] == 1
    assert stats['total_objects'] == 3
    
    service.close()
