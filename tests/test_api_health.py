"""Tests for API health endpoints."""

import pytest
from fastapi.testclient import TestClient
from services.api.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns basic info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Helionyx API"
        assert data["version"] == "0.1.0"
        assert data["status"] == "running"
    
    def test_health_endpoint(self):
        """Test basic health endpoint always returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "helionyx"
    
    def test_health_ready_endpoint_success(self, monkeypatch, tmp_path):
        """Test readiness endpoint returns 200 when dependencies accessible."""
        # Setup: Create test directories
        event_store_path = tmp_path / "events"
        event_store_path.mkdir()
        
        projections_path = tmp_path / "projections"
        projections_path.mkdir()
        
        # Mock config to use test paths
        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("PROJECTIONS_DB_PATH", str(projections_path / "helionyx.db"))
        monkeypatch.setenv("ENV", "dev")
        
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "checks" in data
        assert data["checks"]["event_store"]["accessible"] is True
        assert data["checks"]["projections_db"]["parent_accessible"] is True
    
    def test_health_ready_endpoint_failure(self, monkeypatch, tmp_path):
        """Test readiness endpoint returns 503 when dependencies not accessible."""
        # Setup: Use non-existent paths
        event_store_path = tmp_path / "nonexistent" / "events"
        projections_path = tmp_path / "nonexistent" / "projections"
        
        # Mock config to use non-existent paths
        monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
        monkeypatch.setenv("PROJECTIONS_DB_PATH", str(projections_path / "helionyx.db"))
        monkeypatch.setenv("ENV", "dev")
        
        response = client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert "checks" in data
        # At least one check should fail
        event_store_check = data["checks"]["event_store"]["accessible"]
        projections_check = data["checks"]["projections_db"]["parent_accessible"]
        assert not (event_store_check and projections_check)
    
    def test_health_endpoints_are_fast(self):
        """Test health endpoints respond quickly (smoke test for performance)."""
        import time
        
        # Health endpoint
        start = time.time()
        response = client.get("/health")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 0.1  # Should respond in under 100ms
        
        # Ready endpoint
        start = time.time()
        response = client.get("/health/ready")
        duration = time.time() - start
        
        assert duration < 0.5  # Should respond in under 500ms even with checks
