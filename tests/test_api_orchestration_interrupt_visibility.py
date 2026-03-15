"""Tests for interrupted orchestration visibility in Control Room."""

import asyncio

from fastapi.testclient import TestClient

from services.api.main import app
from services.event_store.file_store import FileEventStore
from shared.contracts import OrchestrationRunCheckpointEvent, OrchestrationRunStartedEvent

client = TestClient(app)


def test_control_room_orchestration_exposes_interrupted_run(monkeypatch, tmp_path):
    event_store_path = tmp_path / "events"
    event_store_path.mkdir()
    db_path = tmp_path / "projections" / "interrupt-visibility.db"
    db_path.parent.mkdir(parents=True)

    monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
    monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
    monkeypatch.setenv("ENV", "dev")

    store = FileEventStore(data_dir=str(event_store_path))
    asyncio.run(
        store.append(
            OrchestrationRunStartedEvent(
                run_id="run-interrupt-001",
                workflow_name="daily_digest",
                trigger="scheduler",
            )
        )
    )
    asyncio.run(
        store.append(
            OrchestrationRunCheckpointEvent(
                run_id="run-interrupt-001",
                workflow_name="daily_digest",
                checkpoint="interrupt_requested",
                details={
                    "reason": "manual_approval_required",
                    "policy_outcome": "escalated",
                    "kind": "delivery_approval",
                },
            )
        )
    )

    response = client.get("/api/v1/control-room/orchestration")
    assert response.status_code == 200
    payload = response.json()

    run = next(item for item in payload["runs"] if item["run_id"] == "run-interrupt-001")
    assert run["status"] == "interrupted"
    assert run["reason"] == "manual_approval_required"
    assert run["interrupt"]["pending"] is True
    assert run["interrupt"]["details"]["kind"] == "delivery_approval"
    assert run["resume"]["eligible"] is True
    assert run["resume"]["pending"] is True
    assert run["resume"]["action"]["path"] == "/api/v1/control-room/orchestration/resume"
    assert payload["summary"]["interrupted_runs"] == 1
