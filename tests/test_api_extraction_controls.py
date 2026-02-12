"""Integration tests for M4 extraction controls.

Verifies:
- ingestion defaults to record-only
- ?extract=true triggers extraction
- /extract/message/{event_id} triggers extraction later and is idempotent-ish
"""

import pytest
from fastapi.testclient import TestClient

from services.api.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _read_event_log_text(event_store_path):
    files = list(event_store_path.glob("*.jsonl"))
    assert files, "Expected at least one event file"
    return "\n".join(p.read_text() for p in files)


def test_ingest_defaults_record_only_no_extraction(monkeypatch, tmp_path, client: TestClient):
    event_store_path = tmp_path / "events"
    event_store_path.mkdir()

    monkeypatch.setenv("ENV", "dev")
    monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
    # Ensure Config.from_env does not load a real key from local .env files.
    monkeypatch.setenv("OPENAI_API_KEY", "")
    # Projections path must exist for Config validation in some flows; keep it valid.
    projections_dir = tmp_path / "projections"
    projections_dir.mkdir()
    monkeypatch.setenv("PROJECTIONS_DB_PATH", str(projections_dir / "helionyx.db"))

    resp = client.post("/api/v1/ingest/message", json={"text": "hello world"})
    assert resp.status_code == 201
    assert resp.json()["status"] == "recorded"

    log_text = _read_event_log_text(event_store_path)
    assert "message_ingested" in log_text
    assert "object_extracted" not in log_text


def test_ingest_extract_true_triggers_extraction(monkeypatch, tmp_path, client: TestClient):
    event_store_path = tmp_path / "events"
    event_store_path.mkdir()

    monkeypatch.setenv("ENV", "dev")
    monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
    monkeypatch.setenv("OPENAI_API_KEY", "")
    projections_dir = tmp_path / "projections"
    projections_dir.mkdir()
    monkeypatch.setenv("PROJECTIONS_DB_PATH", str(projections_dir / "helionyx.db"))

    resp = client.post(
        "/api/v1/ingest/message?extract=true",
        json={"text": "todo: remember to buy groceries"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "recorded_extracted"

    log_text = _read_event_log_text(event_store_path)
    assert "message_ingested" in log_text
    assert "artifact_recorded" in log_text
    assert "object_extracted" in log_text


def test_extract_by_id_endpoint_and_idempotency(monkeypatch, tmp_path, client: TestClient):
    event_store_path = tmp_path / "events"
    event_store_path.mkdir()

    monkeypatch.setenv("ENV", "dev")
    monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
    monkeypatch.setenv("OPENAI_API_KEY", "")
    projections_dir = tmp_path / "projections"
    projections_dir.mkdir()
    monkeypatch.setenv("PROJECTIONS_DB_PATH", str(projections_dir / "helionyx.db"))

    ingest = client.post(
        "/api/v1/ingest/message",
        json={"text": "todo: call the dentist"},
    )
    assert ingest.status_code == 201
    event_id = ingest.json()["event_id"]

    before = _read_event_log_text(event_store_path)
    assert "object_extracted" not in before

    extract1 = client.post(f"/api/v1/extract/message/{event_id}")
    assert extract1.status_code == 200
    assert extract1.json()["status"] == "extracted"

    after1 = _read_event_log_text(event_store_path)
    assert after1.count("object_extracted") >= 1

    # Second trigger should be a no-op-ish
    extract2 = client.post(f"/api/v1/extract/message/{event_id}")
    assert extract2.status_code == 200
    assert extract2.json()["status"] == "no_objects_or_already_extracted"

    after2 = _read_event_log_text(event_store_path)
    assert after2.count("object_extracted") == after1.count("object_extracted")
