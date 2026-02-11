"""Tests for ingestion API endpoints."""

import pytest
from fastapi.testclient import TestClient
from services.api.main import app
from pathlib import Path

client = TestClient(app)


class TestIngestionEndpoints:
    """Test ingestion API endpoints."""
    
    def test_ingest_message_success(self, monkeypatch, tmp_path):
        """Test successful message ingestion."""
        # Setup: Use temp directory for event store
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        
        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("ENV", "dev")
        
        # Ingest a message
        response = client.post(
            "/api/v1/ingest/message",
            json={
                "text": "Remember to buy groceries",
                "source": "api",
                "author": "user",
                "metadata": {"priority": "high"}
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "event_id" in data
        assert data["status"] == "recorded"
        # Event ID should be a valid UUID string
        assert len(data["event_id"]) == 36  # UUID format
    
    def test_ingest_message_minimal(self, monkeypatch, tmp_path):
        """Test message ingestion with minimal required fields."""
        # Setup: Use temp directory for event store
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        
        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("ENV", "dev")
        
        # Ingest with only required field (text)
        response = client.post(
            "/api/v1/ingest/message",
            json={"text": "Simple message"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "event_id" in data
        assert data["status"] == "recorded"
    
    def test_ingest_message_empty_text(self, monkeypatch, tmp_path):
        """Test ingestion fails with empty text."""
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        
        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("ENV", "dev")
        
        response = client.post(
            "/api/v1/ingest/message",
            json={"text": ""}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_ingest_message_missing_text(self, monkeypatch, tmp_path):
        """Test ingestion fails without text field."""
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        
        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("ENV", "dev")
        
        response = client.post(
            "/api/v1/ingest/message",
            json={"source": "api"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_ingest_message_with_conversation_id(self, monkeypatch, tmp_path):
        """Test message ingestion with conversation grouping."""
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        
        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("ENV", "dev")
        
        response = client.post(
            "/api/v1/ingest/message",
            json={
                "text": "This is part of a conversation",
                "source": "api",
                "conversation_id": "conv-123",
                "source_id": "msg-456"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "recorded"
    
    def test_ingest_message_integration(self, monkeypatch, tmp_path):
        """Integration test: verify message is actually written to event store."""
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        
        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("ENV", "dev")
        
        # Ingest a message
        response = client.post(
            "/api/v1/ingest/message",
            json={
                "text": "Integration test message",
                "source": "api",
                "metadata": {"test": True}
            }
        )
        
        assert response.status_code == 201
        
        # Verify event file was created
        event_files = list(event_store_path.glob("*.jsonl"))
        assert len(event_files) > 0, "Event file should be created"
        
        # Verify event was written
        event_file = event_files[0]
        content = event_file.read_text()
        assert "Integration test message" in content
        assert "message_ingested" in content
    
    def test_ingest_multiple_messages(self, monkeypatch, tmp_path):
        """Test ingesting multiple messages sequentially."""
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        
        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("ENV", "dev")
        
        messages = [
            "First message",
            "Second message",
            "Third message"
        ]
        
        event_ids = []
        for msg in messages:
            response = client.post(
                "/api/v1/ingest/message",
                json={"text": msg}
            )
            assert response.status_code == 201
            event_ids.append(response.json()["event_id"])
        
        # All event IDs should be unique
        assert len(event_ids) == len(set(event_ids))
