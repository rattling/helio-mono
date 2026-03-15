"""Tests for orchestration visibility APIs (M12)."""

from fastapi.testclient import TestClient

from services.api.main import app
from services.event_store.file_store import FileEventStore
from shared.contracts import (
    OrchestrationDeliveryFailedEvent,
    OrchestrationDeliverySucceededEvent,
    OrchestrationPolicyAllowedEvent,
    OrchestrationRunFinishedEvent,
    OrchestrationRunStartedEvent,
)

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
    asyncio.run(
        store.append(
            OrchestrationDeliverySucceededEvent(
                run_id="run-visibility-001",
                workflow_name="daily_digest",
                reminder_type="task_daily_digest",
                delivery_channel="telegram",
                details={"sent": True},
            )
        )
    )
    asyncio.run(
        store.append(
            OrchestrationDeliveryFailedEvent(
                run_id="run-visibility-001",
                workflow_name="daily_digest",
                reminder_type="task_daily_digest",
                delivery_channel="email",
                reason="smtp_unavailable",
                details={"partial_success": True},
            )
        )
    )
    asyncio.run(
        store.append(
            OrchestrationRunFinishedEvent(
                run_id="run-visibility-001",
                workflow_name="daily_digest",
                status="completed",
                output={
                    "partial_success": True,
                    "channel_results": [
                        {"delivery_channel": "telegram", "sent": True},
                        {"delivery_channel": "email", "sent": False, "reason": "smtp_unavailable"},
                    ],
                },
            )
        )
    )

    orchestration = client.get("/api/v1/control-room/orchestration")
    assert orchestration.status_code == 200
    payload = orchestration.json()
    assert "runs" in payload
    assert "policy_outcomes" in payload
    assert "delivery_outcomes" in payload
    assert any(item["run_id"] == "run-visibility-001" for item in payload["runs"])
    assert any(item["delivery_channel"] == "email" for item in payload["delivery_outcomes"])
    assert payload["runs"][0]["output"]["partial_success"] is True

    overview = client.get("/api/v1/control-room/overview")
    assert overview.status_code == 200
    overview_payload = overview.json()
    assert "orchestration" in overview_payload
    assert "runs" in overview_payload["orchestration"]
