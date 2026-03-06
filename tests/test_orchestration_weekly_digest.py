"""Weekly digest orchestration-path tests (M12)."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import services.adapters.telegram.scheduler as scheduler
from services.event_store.file_store import FileEventStore
from services.query.service import QueryService
from services.task.service import TaskService
from shared.contracts import EventType, SourceType, TaskIngestRequest, TaskPriority


class _FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 3, 2, 9, 2, 0)


@pytest.mark.asyncio
async def test_weekly_digest_runs_through_orchestration(monkeypatch, tmp_path):
    store = FileEventStore(data_dir=str(tmp_path / "events"))
    query = QueryService(store, db_path=tmp_path / "projections" / "weekly.db")
    task_service = TaskService(event_store=store, query_service=query)
    await task_service.ingest_task(
        TaskIngestRequest(
            title="Weekly digest seed",
            source=SourceType.API,
            source_ref="m12-weekly-001",
            priority=TaskPriority.P1,
        )
    )

    scheduler.event_store = store
    scheduler.query_service = query
    scheduler.db_conn = query.conn
    scheduler.config = SimpleNamespace(
        TELEGRAM_CHAT_ID="12345",
        WEEKLY_SUMMARY_DAY=0,
        WEEKLY_SUMMARY_HOUR=9,
        SHADOW_RANKER_ENABLED=True,
        SHADOW_RANKER_CONFIDENCE_THRESHOLD=0.6,
    )

    send_mock = AsyncMock()
    sleep_mock = AsyncMock()
    monkeypatch.setattr(scheduler, "send_with_retry", send_mock)
    monkeypatch.setattr(scheduler.asyncio, "sleep", sleep_mock)
    monkeypatch.setattr(scheduler, "datetime", _FrozenDateTime)

    await scheduler.check_and_send_weekly_digest(bot=object())

    assert send_mock.await_count == 1
    sleep_mock.assert_awaited()

    events = await store.stream_events()
    event_types = [event.event_type for event in events]
    assert EventType.ORCHESTRATION_RUN_STARTED in event_types
    assert EventType.ORCHESTRATION_POLICY_ALLOWED in event_types
    assert EventType.ORCHESTRATION_DELIVERY_SUCCEEDED in event_types
    assert EventType.ORCHESTRATION_RUN_FINISHED in event_types
    assert EventType.REMINDER_SENT in event_types

    query.close()
