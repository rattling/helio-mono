"""Tests for orchestration visibility APIs (M12)."""

from fastapi.testclient import TestClient

from services.api.main import app
from services.event_store.file_store import FileEventStore
from shared.contracts import OrchestrationPolicyAllowedEvent, OrchestrationRunStartedEvent

client = TestClient(app)


def test_control_room_orchestration_visibility(monkeypatch, tmp_path):
    event_store_path = tmp_path / "events"
    event_store_path.mkdir()
    db_path = tmp_path / "projections" / "orchestration-visibility.db"
    db_path.parent.mkdir(parents=True)

    monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
    monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
    monkeypatch.setenv("ENV", "dev")

    store = FileEventStore(data_dir=str(event_store_path))

    import asyncio

    asyncio.run(
        store.append(
            OrchestrationRunStartedEvent(
                run_id="run-visibility-001",
                workflow_name="daily_digest",
                trigger="scheduler",
            )
        )
    )
    asyncio.run(
        store.append(
            OrchestrationPolicyAllowedEvent(
                run_id="run-visibility-001",
                workflow_name="daily_digest",
                reason="policy_check_passed",
                envelope={"workflow_name": "daily_digest"},
            )
        )
    )

    orchestration = client.get("/api/v1/control-room/orchestration")
    assert orchestration.status_code == 200
    payload = orchestration.json()
    assert "runs" in payload
    assert "policy_outcomes" in payload
    assert any(item["run_id"] == "run-visibility-001" for item in payload["runs"])

    overview = client.get("/api/v1/control-room/overview")
    assert overview.status_code == 200
    overview_payload = overview.json()
    assert "orchestration" in overview_payload
    assert "runs" in overview_payload["orchestration"]
