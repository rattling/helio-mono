"""Tests for Control Room transparency API (Milestone 9)."""

from fastapi.testclient import TestClient

from services.api.main import app

client = TestClient(app)


def test_control_room_overview_shape(monkeypatch, tmp_path):
    event_store_path = tmp_path / "events"
    event_store_path.mkdir()
    db_path = tmp_path / "projections" / "control-room.db"
    db_path.parent.mkdir(parents=True)

    monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
    monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
    monkeypatch.setenv("ENV", "dev")

    ingest = client.post(
        "/api/v1/tasks/ingest",
        json={
            "title": "Control room seed task",
            "source": "api",
            "source_ref": "control-room-001",
            "priority": "p1",
        },
    )
    assert ingest.status_code == 201

    response = client.get("/api/v1/control-room/overview")
    assert response.status_code == 200
    payload = response.json()

    assert payload["health"]["status"] == "healthy"
    assert payload["readiness"]["status"] in {"ready", "not_ready"}
    assert "checks" in payload["readiness"]
    assert "event_store" in payload["readiness"]["checks"]
    assert "projections_db" in payload["readiness"]["checks"]

    assert "top_actionable" in payload["attention_today"]
    assert "due_this_week" in payload["attention_week"]

    top_actionable = payload["attention_today"].get("top_actionable", [])
    if top_actionable:
        item = top_actionable[0]
        assert "ranking_explanation" in item
        assert "personalization_applied" in item

    assert "generated_at" in payload
