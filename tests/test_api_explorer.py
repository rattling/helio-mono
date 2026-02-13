"""Tests for Data Explorer API endpoints (Milestone 10)."""

from fastapi.testclient import TestClient

from services.api.main import app

client = TestClient(app)


def _seed_task(source_ref: str, monkeypatch, tmp_path):
    event_store_path = tmp_path / "events"
    event_store_path.mkdir(exist_ok=True)
    db_path = tmp_path / "projections" / "explorer.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
    monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
    monkeypatch.setenv("ENV", "dev")

    response = client.post(
        "/api/v1/tasks/ingest",
        json={
            "title": "Explorer target task",
            "body": "Investigate timeline",
            "source": "api",
            "source_ref": source_ref,
            "priority": "p1",
        },
    )
    assert response.status_code == 201
    return response.json()["task_id"]


def test_explorer_lookup_task(monkeypatch, tmp_path):
    task_id = _seed_task("explorer-lookup-001", monkeypatch, tmp_path)

    response = client.get(f"/api/v1/explorer/lookup?entity_type=task&entity_id={task_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["entity_type"] == "task"
    assert payload["entity_id"] == task_id
    assert payload["canonical"]["task_id"] == task_id


def test_explorer_lookup_event_invalid_uuid(monkeypatch, tmp_path):
    _seed_task("explorer-lookup-002", monkeypatch, tmp_path)

    response = client.get("/api/v1/explorer/lookup?entity_type=event&entity_id=not-a-uuid")
    assert response.status_code == 422


def test_explorer_timeline_state_and_decision(monkeypatch, tmp_path):
    task_id = _seed_task("explorer-timeline-001", monkeypatch, tmp_path)

    complete = client.post(f"/api/v1/tasks/{task_id}/complete")
    assert complete.status_code == 200

    timeline = client.get(f"/api/v1/explorer/timeline?entity_type=task&entity_id={task_id}")
    assert timeline.status_code == 200
    timeline_payload = timeline.json()
    assert timeline_payload["events"]

    timestamps = [item["timestamp"] for item in timeline_payload["events"]]
    assert timestamps == sorted(timestamps)

    state = client.get(f"/api/v1/explorer/state?entity_type=task&entity_id={task_id}")
    assert state.status_code == 200
    state_payload = state.json()
    assert state_payload["snapshot"]["task_id"] == task_id
    assert state_payload["traceability"]["event_count"] >= 1
    assert isinstance(state_payload["traceability"]["event_ids"], list)

    decision = client.get(f"/api/v1/explorer/decision?entity_type=task&entity_id={task_id}")
    assert decision.status_code == 200
    decision_payload = decision.json()
    assert isinstance(decision_payload["decisions"], list)
    assert any("decision" in item["event_type"] for item in decision_payload["decisions"])
