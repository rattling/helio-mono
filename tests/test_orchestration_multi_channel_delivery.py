"""Tests for M13 multi-channel digest delivery orchestration."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import services.adapters.telegram.scheduler as scheduler
from services.api.routes.control_room import _orchestration_visibility
from services.event_store.file_store import FileEventStore
from services.query.service import QueryService
from services.task.service import TaskService
from shared.common.config import Config
from shared.contracts import EventType, SourceType, TaskIngestRequest, TaskPriority


class _FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 3, 2, 20, 2, 0)


@pytest.mark.asyncio
async def test_multi_channel_delivery_records_partial_success(monkeypatch, tmp_path):
    store = FileEventStore(data_dir=str(tmp_path / "events"))
    query = QueryService(store, db_path=tmp_path / "projections" / "multi-channel.db")
    task_service = TaskService(event_store=store, query_service=query)
    await task_service.ingest_task(
        TaskIngestRequest(
            title="Digest seed",
            source=SourceType.API,
            source_ref="m13-multi-001",
            priority=TaskPriority.P1,
        )
    )

    scheduler.event_store = store
    scheduler.query_service = query
    scheduler.db_conn = query.conn
    scheduler.config = SimpleNamespace(
        TELEGRAM_CHAT_ID="12345",
        DAILY_SUMMARY_HOUR=20,
        SHADOW_RANKER_ENABLED=True,
        SHADOW_RANKER_CONFIDENCE_THRESHOLD=0.6,
        EMAIL_SMTP_HOST="smtp.gmail.com",
        EMAIL_SMTP_PORT=587,
        EMAIL_SMTP_USERNAME="ops@example.com",
        EMAIL_SMTP_PASSWORD="secret",
        EMAIL_FROM_ADDRESS="ops@example.com",
        EMAIL_TO_ADDRESS="john@example.com",
        EMAIL_USE_TLS=True,
    )

    send_mock = AsyncMock()
    email_mock = AsyncMock(side_effect=RuntimeError("smtp_unavailable"))
    sleep_mock = AsyncMock()
    monkeypatch.setattr(scheduler, "send_with_retry", send_mock)
    monkeypatch.setattr(scheduler, "send_email_smtp", email_mock)
    monkeypatch.setattr(scheduler.asyncio, "sleep", sleep_mock)
    monkeypatch.setattr(scheduler, "datetime", _FrozenDateTime)

    await scheduler.check_and_send_daily_digest(bot=object())

    assert send_mock.await_count == 1
    assert email_mock.await_count == 1

    events = await store.stream_events()
    succeeded_channels = {
        str(getattr(event, "delivery_channel", ""))
        for event in events
        if event.event_type == EventType.ORCHESTRATION_DELIVERY_SUCCEEDED
    }
    failed_channels = {
        str(getattr(event, "delivery_channel", ""))
        for event in events
        if event.event_type == EventType.ORCHESTRATION_DELIVERY_FAILED
    }
    reminder_channels = {
        str(getattr(event, "delivery_channel", ""))
        for event in events
        if event.event_type == EventType.REMINDER_SENT
    }

    assert succeeded_channels == {"telegram"}
    assert failed_channels == {"email"}
    assert reminder_channels == {"telegram"}

    monkeypatch.setenv("EVENT_STORE_PATH", str(tmp_path / "events"))
    monkeypatch.setenv("PROJECTIONS_DB_PATH", str(tmp_path / "projections" / "multi-channel.db"))
    monkeypatch.setenv("ENV", "dev")
    visibility = await _orchestration_visibility(Config.from_env(), limit=10)
    run = visibility["runs"][0]
    assert run["status"] == "completed"
    assert run["output"]["partial_success"] is True
    assert {item["delivery_channel"] for item in visibility["delivery_outcomes"]} == {
        "telegram",
        "email",
    }

    query.close()
