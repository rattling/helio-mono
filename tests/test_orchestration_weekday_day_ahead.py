"""Tests for the M13 weekday day-ahead orchestration path."""

from datetime import datetime
from types import SimpleNamespace

import pytest

import services.adapters.telegram.scheduler as scheduler
from services.event_store.file_store import FileEventStore
from services.query.service import QueryService
from services.task.service import TaskService
from shared.contracts import EventType, SourceType, TaskIngestRequest, TaskPriority


@pytest.mark.asyncio
async def test_daily_digest_builds_weekday_day_ahead_payload(tmp_path):
    store = FileEventStore(data_dir=str(tmp_path / "events"))
    query = QueryService(store, db_path=tmp_path / "projections" / "weekday.db")
    task_service = TaskService(event_store=store, query_service=query)
    await task_service.ingest_task(
        TaskIngestRequest(
            title="Weekday planning seed",
            source=SourceType.API,
            source_ref="m13-weekday-001",
            priority=TaskPriority.P1,
            due_at="2026-03-19T09:00:00",
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
        ATTENTION_URGENT_THRESHOLD=60.0,
        GOOGLE_CALENDAR_ACCESS_TOKEN=None,
        GOOGLE_CALENDAR_ID=None,
        ZOHO_CALENDAR_ACCESS_TOKEN=None,
        ZOHO_CALENDAR_ID=None,
    )

    result = await scheduler.run_orchestration_workflow(
        bot=None,
        workflow_name="daily_digest",
        dry_run=True,
    )

    assert result["status"] == "completed"
    assert result["result"]["digest_type"] == "weekday_day_ahead"
    assert result["result"]["calendar_status"]["google"] == "unconfigured"
    assert result["result"]["calendar_status"]["zoho"] == "unconfigured"

    events = await store.stream_events()
    completed_nodes = [
        getattr(event, "node_id", "")
        for event in events
        if event.event_type == EventType.ORCHESTRATION_NODE_COMPLETED
    ]
    assert "context_gather" in completed_nodes
    assert "delivery_prepare" in completed_nodes

    query.close()
