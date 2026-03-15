"""Tests for resume metadata visibility in Control Room."""

import asyncio

from fastapi.testclient import TestClient

from services.api.main import app
from services.event_store.file_store import FileEventStore
from shared.contracts import OrchestrationRunCheckpointEvent, OrchestrationRunStartedEvent

client = TestClient(app)


def test_control_room_orchestration_exposes_resume_decision(monkeypatch, tmp_path):
    event_store_path = tmp_path / "events"
    event_store_path.mkdir()
    db_path = tmp_path / "projections" / "resume-visibility.db"
    db_path.parent.mkdir(parents=True)

    monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
    monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
    monkeypatch.setenv("ENV", "dev")

    store = FileEventStore(data_dir=str(event_store_path))
    asyncio.run(
        store.append(
            OrchestrationRunStartedEvent(
                run_id="run-resume-001",
                workflow_name="weekly_digest",
                trigger="scheduler",
            )
        )
    )
    asyncio.run(
        store.append(
            OrchestrationRunCheckpointEvent(
                run_id="run-resume-001",
                workflow_name="weekly_digest",
                checkpoint="interrupt_requested",
                details={"reason": "manual_approval_required", "kind": "policy_escalation"},
            )
        )
    )
    asyncio.run(
        store.append(
            OrchestrationRunCheckpointEvent(
                run_id="run-resume-001",
                workflow_name="weekly_digest",
                checkpoint="interrupt_resumed",
                details={"approved": True},
            )
        )
    )

    response = client.get("/api/v1/control-room/orchestration")
    assert response.status_code == 200
    payload = response.json()

    run = next(item for item in payload["runs"] if item["run_id"] == "run-resume-001")
    assert run["status"] == "in_progress"
    assert run["interrupt"]["pending"] is False
    assert run["interrupt"]["resumed_at"]
    assert run["resume"]["eligible"] is False
    assert run["resume"]["pending"] is False
    assert run["resume"]["last_decision"]["approved"] is True
