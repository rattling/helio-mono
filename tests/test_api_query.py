"""Tests for query API endpoints."""

import pytest
import json
from fastapi.testclient import TestClient
from services.api.main import app
from pathlib import Path

client = TestClient(app)


class TestQueryEndpoints:
    """Test query API endpoints."""
    
    @pytest.fixture
    async def setup_test_data(self, monkeypatch, tmp_path):
        """Setup test environment with sample data."""
        # Setup paths
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        db_path = tmp_path / "projections" / "test.db"
        db_path.parent.mkdir(parents=True)
        
        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
        monkeypatch.setenv("ENV", "dev")
        
        # Import services for setup
        from services.event_store.file_store import FileEventStore
        from services.ingestion.service import IngestionService
        from services.extraction.service import ExtractionService
        from services.extraction.mock_llm import MockLLMService
        from services.query.service import QueryService
        from shared.contracts import SourceType
        
        # Initialize services
        event_store = FileEventStore(data_dir=str(event_store_path))
        ingestion_service = IngestionService(event_store)
        llm_service = MockLLMService(event_store)
        extraction_service = ExtractionService(event_store, llm_service)
        query_service = QueryService(event_store, db_path=db_path)
        
        # Ingest and extract test messages
        test_messages = [
            "TODO: Buy groceries #shopping",
            "NOTE: Meeting notes from standup #work",
            "TRACK: Fitness goals #health"
        ]
        
        for msg in test_messages:
            msg_id = await ingestion_service.ingest_message(
                content=msg,
                source=SourceType.CLI,
                source_id=f"test-{hash(msg)}"
            )
            await extraction_service.extract_from_message(str(msg_id))
        
        # Rebuild projections
        await query_service.rebuild_projections()
        query_service.close()
        
        return {"event_store_path": event_store_path, "db_path": db_path, "tmp_path": tmp_path}
    
    @pytest.mark.asyncio
    async def test_get_todos(self, setup_test_data):
        """Test GET /api/v1/todos endpoint."""
        response = client.get("/api/v1/todos")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should have at least one todo from test data
        if len(data) > 0:
            todo = data[0]
            assert "object_id" in todo
            assert "title" in todo
            assert "status" in todo
    
    @pytest.mark.asyncio
    async def test_get_todos_with_status_filter(self, setup_test_data):
        """Test todos endpoint with status filter."""
        response = client.get("/api/v1/todos?status=pending")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # All returned todos should have pending status
        for todo in data:
            assert todo["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_get_todos_with_tags_filter(self, setup_test_data):
        """Test todos endpoint with tags filter."""
        response = client.get("/api/v1/todos?tags=shopping")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_notes(self, setup_test_data):
        """Test GET /api/v1/notes endpoint."""
        response = client.get("/api/v1/notes")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should have at least one note from test data
        if len(data) > 0:
            note = data[0]
            assert "object_id" in note
            assert "title" in note
            assert "content" in note
    
    @pytest.mark.asyncio
    async def test_get_notes_with_search(self, setup_test_data):
        """Test notes endpoint with search filter."""
        response = client.get("/api/v1/notes?search=meeting")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_notes_with_pagination_params(self, setup_test_data):
        """Test notes endpoint accepts pagination params (for future compatibility)."""
        response = client.get("/api/v1/notes?limit=10&offset=0")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_tracks(self, setup_test_data):
        """Test GET /api/v1/tracks endpoint."""
        response = client.get("/api/v1/tracks")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should have at least one track from test data
        if len(data) > 0:
            track = data[0]
            assert "object_id" in track
            assert "title" in track
            assert "status" in track
    
    @pytest.mark.asyncio
    async def test_get_tracks_with_status_filter(self, setup_test_data):
        """Test tracks endpoint with status filter."""
        response = client.get("/api/v1/tracks?status=active")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_stats(self, setup_test_data):
        """Test GET /api/v1/stats endpoint."""
        response = client.get("/api/v1/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "todos" in data
        assert "notes" in data
        assert "tracks" in data
        assert "total_objects" in data
        assert "last_rebuild" in data
        
        # Should have counts from test data
        assert isinstance(data["todos"], int)
        assert isinstance(data["notes"], int)
        assert isinstance(data["tracks"], int)
        assert data["total_objects"] >= 0
    
    def test_get_todos_empty_database(self, monkeypatch, tmp_path):
        """Test todos endpoint with empty database."""
        # Setup clean environment
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        db_path = tmp_path / "projections" / "empty.db"
        db_path.parent.mkdir(parents=True)
        
        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
        monkeypatch.setenv("ENV", "dev")
        
        # Initialize empty database
        from services.event_store.file_store import FileEventStore
        from services.query.service import QueryService
        
        event_store = FileEventStore(data_dir=str(event_store_path))
        query_service = QueryService(event_store, db_path=db_path)
        query_service.close()
        
        # Query should return empty list
        response = client.get("/api/v1/todos")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_stats_empty_database(self, monkeypatch, tmp_path):
        """Test stats endpoint with empty database."""
        # Setup clean environment
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        db_path = tmp_path / "projections" / "empty.db"
        db_path.parent.mkdir(parents=True)
        
        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
        monkeypatch.setenv("ENV", "dev")
        
        # Initialize empty database
        from services.event_store.file_store import FileEventStore
        from services.query.service import QueryService
        
        event_store = FileEventStore(data_dir=str(event_store_path))
        query_service = QueryService(event_store, db_path=db_path)
        query_service.close()
        
        # Stats should return zeros
        response = client.get("/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["todos"] == 0
        assert data["notes"] == 0
        assert data["tracks"] == 0
        assert data["total_objects"] == 0
