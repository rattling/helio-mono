"""Tests for M13 shared graph reuse across existing orchestration flows."""

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

import services.adapters.telegram.scheduler as scheduler
from services.event_store.file_store import FileEventStore
from services.query.service import QueryService
from services.task.service import TaskService
from shared.contracts import EventType, SourceType, TaskIngestRequest, TaskPriority


@pytest.mark.asyncio
async def test_existing_flows_use_shared_m13_graph_primitives(monkeypatch, tmp_path):
    store = FileEventStore(data_dir=str(tmp_path / "events"))
    query = QueryService(store, db_path=tmp_path / "projections" / "flow-reuse.db")
    task_service = TaskService(event_store=store, query_service=query)
    await task_service.ingest_task(
        TaskIngestRequest(
            title="Digest seed",
            source=SourceType.API,
            source_ref="m13-flow-daily-001",
            priority=TaskPriority.P1,
        )
    )
    await task_service.ingest_task(
        TaskIngestRequest(
            title="Urgent seed",
            source=SourceType.API,
            source_ref="m13-flow-urgent-001",
            priority=TaskPriority.P0,
            due_at=datetime.utcnow() + timedelta(hours=2),
        )
    )

    scheduler.event_store = store
    scheduler.query_service = query
    scheduler.db_conn = query.conn
    scheduler.config = SimpleNamespace(
        TELEGRAM_CHAT_ID="12345",
        SHADOW_RANKER_ENABLED=True,
        SHADOW_RANKER_CONFIDENCE_THRESHOLD=0.6,
        ATTENTION_URGENT_THRESHOLD=60.0,
    )

    daily = await scheduler.run_orchestration_workflow(
        bot=None,
        workflow_name="daily_digest",
        dry_run=True,
    )
    weekly = await scheduler.run_orchestration_workflow(
        bot=None,
        workflow_name="weekly_digest",
        dry_run=True,
    )
    urgent = await scheduler.run_orchestration_workflow(
        bot=None,
        workflow_name="urgent_reminder",
        dry_run=True,
    )

    assert daily["status"] == "completed"
    assert weekly["status"] == "completed"
    assert urgent["status"] == "completed"

    events = await store.stream_events()
    completed_nodes_by_run: dict[str, set[str]] = {}
    for event in events:
        if event.event_type != EventType.ORCHESTRATION_NODE_COMPLETED:
            continue
        run_id = str(getattr(event, "run_id", ""))
        completed_nodes_by_run.setdefault(run_id, set()).add(str(getattr(event, "node_id", "")))

    required_nodes = {
        "context_gather",
        "policy_evaluation",
        "delivery_prepare",
        "delivery_execution",
    }
    for result in (daily, weekly, urgent):
        assert required_nodes.issubset(completed_nodes_by_run[result["run_id"]])

    query.close()
