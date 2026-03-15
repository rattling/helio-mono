"""Tests for degraded orchestration visibility in Control Room."""

import asyncio

from fastapi.testclient import TestClient

from services.api.main import app
from services.event_store.file_store import FileEventStore
from shared.contracts import (
    OrchestrationDeliveryFailedEvent,
    OrchestrationDeliverySucceededEvent,
    OrchestrationRunFinishedEvent,
    OrchestrationRunStartedEvent,
)

client = TestClient(app)


def test_control_room_orchestration_exposes_degraded_and_partial_delivery(monkeypatch, tmp_path):
    event_store_path = tmp_path / "events"
    event_store_path.mkdir()
    db_path = tmp_path / "projections" / "degraded-visibility.db"
    db_path.parent.mkdir(parents=True)

    monkeypatch.setenv("EVENT_STORE_PATH", str(event_store_path))
    monkeypatch.setenv("PROJECTIONS_DB_PATH", str(db_path))
    monkeypatch.setenv("ENV", "dev")

    store = FileEventStore(data_dir=str(event_store_path))
    asyncio.run(
        store.append(
            OrchestrationRunStartedEvent(
                run_id="run-degraded-001",
                workflow_name="daily_digest",
                trigger="scheduler",
            )
        )
    )
    asyncio.run(
        store.append(
            OrchestrationDeliverySucceededEvent(
                run_id="run-degraded-001",
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
                run_id="run-degraded-001",
                workflow_name="daily_digest",
                reminder_type="task_daily_digest",
                delivery_channel="email",
                reason="smtp_unavailable",
                details={"digest_type": "weekday_day_ahead"},
            )
        )
    )
    asyncio.run(
        store.append(
            OrchestrationRunFinishedEvent(
                run_id="run-degraded-001",
                workflow_name="daily_digest",
                status="completed",
                output={
                    "partial_success": True,
                    "calendar_degraded": True,
                    "calendar_status": {"google": "ok", "zoho": "degraded"},
                    "sent_channels": ["telegram"],
                    "failed_channels": ["email"],
                    "channel_results": [
                        {"delivery_channel": "telegram", "sent": True},
                        {
                            "delivery_channel": "email",
                            "sent": False,
                            "reason": "smtp_unavailable",
                        },
                    ],
                },
            )
        )
    )

    orchestration = client.get("/api/v1/control-room/orchestration")
    assert orchestration.status_code == 200
    payload = orchestration.json()

    run = next(item for item in payload["runs"] if item["run_id"] == "run-degraded-001")
    assert run["status"] == "completed"
    assert run["degraded"] is True
    assert run["partial_delivery"] is True
    assert "calendar_provider_degraded" in run["degraded_reasons"]
    assert "partial_delivery" in run["degraded_reasons"]
    assert "calendar:zoho:degraded" in run["degraded_reasons"]
    assert run["delivery"]["succeeded_channels"] == ["telegram"]
    assert run["delivery"]["failed_channels"] == ["email"]
    assert payload["summary"]["degraded_runs"] == 1
    assert payload["summary"]["partial_delivery_runs"] == 1

    overview = client.get("/api/v1/control-room/overview")
    assert overview.status_code == 200
    overview_payload = overview.json()
    overview_run = next(
        item
        for item in overview_payload["orchestration"]["runs"]
        if item["run_id"] == "run-degraded-001"
    )
    assert overview_run["degraded"] is True
    assert overview_run["partial_delivery"] is True
