"""Tests for extraction service with LLM integration."""

import pytest
from uuid import uuid4

from shared.contracts import MessageIngestedEvent, SourceType
from shared.contracts.objects import ExtractionResult
from services.extraction.service import ExtractionService
from services.extraction.mock_llm import MockLLMService
from services.event_store.file_store import FileEventStore


@pytest.fixture
async def event_store(tmp_path):
    """Create a temporary event store."""
    store = FileEventStore(data_dir=str(tmp_path / "events"))
    return store


@pytest.fixture
async def llm_service(event_store):
    """Create a mock LLM service."""
    return MockLLMService(event_store)


@pytest.fixture
async def extraction_service(event_store, llm_service):
    """Create an extraction service with mock LLM."""
    return ExtractionService(event_store, llm_service)


@pytest.mark.asyncio
async def test_extract_todo_from_message(event_store, extraction_service):
    """Test extracting a todo from a message."""
    # Ingest a message with todo keyword
    message_event = MessageIngestedEvent(
        content="Remind me to review the quarterly reports by end of week",
        source=SourceType.CLI,
        source_id="test-1",
        author="test-user",
    )
    message_id = await event_store.append(message_event)

    # Extract objects
    extracted_items = await extraction_service.extract_from_message(message_id)

    # Should extract one todo
    assert len(extracted_items) > 0

    # Verify the extracted object
    event_id, object_type, object_data = extracted_items[0]
    assert object_type == "todo"
    assert "review" in object_data["title"].lower()


@pytest.mark.asyncio
async def test_extract_note_from_message(event_store, extraction_service):
    """Test extracting a note from a message."""
    message_event = MessageIngestedEvent(
        content="Note: The API documentation is at docs.example.com",
        source=SourceType.CLI,
        source_id="test-2",
        author="test-user",
    )
    message_id = await event_store.append(message_event)

    extracted_items = await extraction_service.extract_from_message(message_id)

    assert len(extracted_items) > 0
    event_id, object_type, object_data = extracted_items[0]
    assert object_type == "note"
    assert "documentation" in object_data["title"].lower()


@pytest.mark.asyncio
async def test_extract_track_from_message(event_store, extraction_service):
    """Test extracting a tracking item from a message."""
    message_event = MessageIngestedEvent(
        content="Track progress on the database migration project",
        source=SourceType.CLI,
        source_id="test-3",
        author="test-user",
    )
    message_id = await event_store.append(message_event)

    extracted_items = await extraction_service.extract_from_message(message_id)

    assert len(extracted_items) > 0
    event_id, object_type, object_data = extracted_items[0]
    assert object_type == "track"
    assert "migration" in object_data["title"].lower()


@pytest.mark.asyncio
async def test_extract_no_objects_from_plain_message(event_store, extraction_service):
    """Test that plain messages without keywords extract nothing."""
    message_event = MessageIngestedEvent(
        content="Hello, how are you today?",
        source=SourceType.CLI,
        source_id="test-4",
        author="test-user",
    )
    message_id = await event_store.append(message_event)

    extracted_items = await extraction_service.extract_from_message(message_id)

    # Should not extract anything from a plain greeting
    assert len(extracted_items) == 0


@pytest.mark.asyncio
async def test_extract_with_invalid_message_id(extraction_service):
    """Test extraction with non-existent message ID."""
    fake_id = uuid4()
    extracted_items = await extraction_service.extract_from_message(fake_id)

    # Should return empty list
    assert extracted_items == []


@pytest.mark.asyncio
async def test_mock_llm_records_artifacts(event_store, extraction_service):
    """Test that mock LLM records prompt and response artifacts."""
    message_event = MessageIngestedEvent(
        content="Todo: Complete the project documentation",
        source=SourceType.CLI,
        source_id="test-5",
        author="test-user",
    )
    message_id = await event_store.append(message_event)

    # Count events before extraction
    events_before = await event_store.stream_events()

    # Extract objects
    await extraction_service.extract_from_message(message_id)

    # Count events after extraction
    events_after = await event_store.stream_events()

    # Should have added:
    # - 2 artifact events (prompt + response)
    # - 1 object extracted event
    assert len(events_after) >= len(events_before) + 3


@pytest.mark.asyncio
async def test_extraction_result_includes_metadata(event_store, llm_service):
    """Test that extraction results include proper metadata."""
    result = await llm_service.extract_objects("Todo: Write unit tests for the extraction service")

    assert isinstance(result, ExtractionResult)
    assert result.model_used == "mock-llm"
    assert result.tokens_used > 0
    assert result.confidence > 0
    assert result.prompt_artifact_id is not None
    assert result.response_artifact_id is not None
    assert result.extraction_metadata.get("mock") is True


@pytest.mark.asyncio
async def test_extraction_priority_detection(event_store, extraction_service):
    """Test that urgent keywords are detected in todos."""
    message_event = MessageIngestedEvent(
        content="URGENT: Todo Fix the production bug immediately",
        source=SourceType.CLI,
        source_id="test-6",
        author="test-user",
    )
    message_id = await event_store.append(message_event)

    extracted_items = await extraction_service.extract_from_message(message_id)

    assert len(extracted_items) > 0
    event_id, object_type, object_data = extracted_items[0]

    # Check priority is elevated
    assert object_data["priority"] == "urgent"


@pytest.mark.asyncio
async def test_mock_llm_call_counting(event_store):
    """Test that mock LLM tracks call count."""
    llm = MockLLMService(event_store)

    assert llm.call_count == 0

    await llm.extract_objects("First message")
    assert llm.call_count == 1

    await llm.extract_objects("Second message")
    assert llm.call_count == 2


@pytest.mark.asyncio
async def test_extraction_with_context(event_store, llm_service):
    """Test extraction with additional context."""
    context = {
        "conversation_history": ["Previous message 1", "Previous message 2"],
        "user_preferences": {"timezone": "UTC"},
    }

    result = await llm_service.extract_objects("Todo: Schedule meeting", context=context)

    # Should still extract successfully with context
    assert isinstance(result, ExtractionResult)
    assert len(result.objects) > 0
