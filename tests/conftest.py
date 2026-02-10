"""Shared pytest fixtures for all tests."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from services.event_store.file_store import FileEventStore
from services.extraction.mock_llm import MockLLMService
from services.extraction.service import ExtractionService
from services.query.service import QueryService
from services.ingestion.service import IngestionService


@pytest.fixture
def tmp_event_store(tmp_path):
    """Create a temporary event store for testing.
    
    Uses pytest's tmp_path fixture for automatic cleanup.
    """
    store = FileEventStore(data_dir=str(tmp_path / "events"))
    return store


@pytest.fixture
async def event_store(tmp_path):
    """Create a temporary async event store for testing.
    
    Uses pytest's tmp_path fixture for automatic cleanup.
    """
    store = FileEventStore(data_dir=str(tmp_path / "events"))
    return store


@pytest.fixture
def temp_db(tmp_path):
    """Create temporary SQLite database for tests.
    
    Automatically cleaned up by pytest's tmp_path.
    """
    db_path = tmp_path / "test.db"
    return db_path


@pytest.fixture
def temp_event_store(tmp_path):
    """Create temporary event store for tests.
    
    Non-async version for synchronous tests.
    """
    store = FileEventStore(data_dir=str(tmp_path / "events"))
    return store


@pytest.fixture
async def mock_llm_service(event_store):
    """Create a mock LLM service for testing extraction."""
    return MockLLMService(event_store)


@pytest.fixture
async def extraction_service(event_store, mock_llm_service):
    """Create an extraction service with mock LLM."""
    return ExtractionService(event_store, mock_llm_service)


@pytest.fixture
async def query_service(event_store, temp_db):
    """Create a query service with temporary database."""
    service = QueryService(event_store, db_path=temp_db)
    yield service
    service.close()


@pytest.fixture
async def ingestion_service(event_store):
    """Create an ingestion service."""
    return IngestionService(event_store)


@pytest.fixture
def mock_telegram_update():
    """Create a mock Telegram Update object."""
    update = MagicMock()
    update.effective_chat.id = 123456789
    update.effective_user.username = "test_user"
    update.message.text = "Test message"
    return update


@pytest.fixture
def mock_telegram_context():
    """Create a mock Telegram CallbackContext."""
    context = MagicMock()
    return context


@pytest.fixture
def sample_todo():
    """Sample todo object for testing."""
    return {
        'object_id': 'todo-123',
        'title': 'Test todo',
        'description': 'This is a test',
        'status': 'pending',
        'priority': 'high',
        'due_date': '2026-02-15T10:00:00Z',
        'created_at': '2026-02-10T09:00:00Z',
        'tags': '["work", "urgent"]'
    }


@pytest.fixture
def sample_note():
    """Sample note object for testing."""
    return {
        'object_id': 'note-456',
        'title': 'Test note',
        'content': 'This is a test note content',
        'created_at': '2026-02-10T09:00:00Z',
        'tags': '["ideas"]'
    }


@pytest.fixture
def sample_track():
    """Sample track object for testing."""
    return {
        'object_id': 'track-789',
        'name': 'Test tracking item',
        'category': 'health',
        'status': 'active',
        'value': 75.5,
        'unit': 'kg',
        'created_at': '2026-02-10T09:00:00Z',
        'tags': '["fitness"]'
    }
