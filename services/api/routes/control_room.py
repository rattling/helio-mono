"""Control Room read-only transparency endpoints (Milestone 9)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from collections.abc import Generator

from fastapi import APIRouter, Depends, Query

from shared.common.config import Config
from shared.contracts import ControlRoomOverview, EventType, ReadinessCheck, ReadinessPayload
from services.attention import AttentionService
from services.event_store.file_store import FileEventStore
from services.query.service import QueryService
from services.adapters.telegram import scheduler as telegram_scheduler

router = APIRouter()


def get_control_room_services() -> Generator[tuple[Config, AttentionService], None, None]:
    """Get configured services used for control room payloads."""
    config = Config.from_env()
    event_store = FileEventStore(data_dir=config.EVENT_STORE_PATH)
    query_service = QueryService(event_store, db_path=Path(config.PROJECTIONS_DB_PATH))
    try:
        attention_service = AttentionService(
            event_store=event_store,
            query_service=query_service,
            enable_shadow_ranker=getattr(config, "SHADOW_RANKER_ENABLED", True),
            shadow_confidence_threshold=getattr(config, "SHADOW_RANKER_CONFIDENCE_THRESHOLD", 0.6),
            enable_bounded_personalization=getattr(
                config, "ATTENTION_BOUNDED_PERSONALIZATION_ENABLED", False
            ),
        )
        yield config, attention_service
    finally:
        query_service.close()


def _readiness_from_config(config: Config) -> ReadinessPayload:
    event_store_path = Path(config.EVENT_STORE_PATH)
    projections_db_path = Path(config.PROJECTIONS_DB_PATH)

    checks = {
        "event_store": ReadinessCheck(
            path=str(event_store_path),
            accessible=event_store_path.exists() or event_store_path.parent.exists(),
        ),
        "projections_db": ReadinessCheck(
            path=str(projections_db_path),
            parent_accessible=projections_db_path.parent.exists(),
        ),
    }

    all_ready = bool(
        checks["event_store"].accessible and checks["projections_db"].parent_accessible
    )
    return ReadinessPayload(status="ready" if all_ready else "not_ready", checks=checks)


async def _orchestration_visibility(config: Config, limit: int = 25) -> dict:
    event_store = FileEventStore(data_dir=config.EVENT_STORE_PATH)
    orchestration_events = await event_store.stream_events(
        event_types=[
            EventType.ORCHESTRATION_RUN_STARTED,
            EventType.ORCHESTRATION_RUN_CHECKPOINT,
            EventType.ORCHESTRATION_RUN_FINISHED,
            EventType.ORCHESTRATION_RUN_FAILED,
            EventType.ORCHESTRATION_POLICY_ALLOWED,
            EventType.ORCHESTRATION_POLICY_BLOCKED,
            EventType.ORCHESTRATION_POLICY_ESCALATED,
            EventType.ORCHESTRATION_DELIVERY_ATTEMPTED,
            EventType.ORCHESTRATION_DELIVERY_SUCCEEDED,
            EventType.ORCHESTRATION_DELIVERY_FAILED,
        ]
    )
    orchestration_events = sorted(orchestration_events, key=lambda item: item.timestamp)

    run_status: dict[str, dict] = {}
    policy_outcomes: list[dict] = []
    delivery_outcomes: list[dict] = []

    for event in orchestration_events:
        run_id = str(getattr(event, "run_id", ""))
        workflow_name = str(getattr(event, "workflow_name", ""))

        if event.event_type == EventType.ORCHESTRATION_RUN_STARTED:
            run_status[run_id] = {
                "run_id": run_id,
                "workflow_name": workflow_name,
                "started_at": event.timestamp.isoformat(),
                "status": "in_progress",
            }
        elif event.event_type == EventType.ORCHESTRATION_RUN_FINISHED:
            run_status.setdefault(run_id, {"run_id": run_id, "workflow_name": workflow_name})
            run_status[run_id]["status"] = "completed"
            run_status[run_id]["finished_at"] = event.timestamp.isoformat()
        elif event.event_type == EventType.ORCHESTRATION_RUN_FAILED:
            run_status.setdefault(run_id, {"run_id": run_id, "workflow_name": workflow_name})
            run_status[run_id]["status"] = "failed"
            run_status[run_id]["finished_at"] = event.timestamp.isoformat()
            run_status[run_id]["reason"] = str(getattr(event, "reason", "unknown"))

        if event.event_type in {
            EventType.ORCHESTRATION_POLICY_ALLOWED,
            EventType.ORCHESTRATION_POLICY_BLOCKED,
            EventType.ORCHESTRATION_POLICY_ESCALATED,
        }:
            policy_outcomes.append(
                {
                    "run_id": run_id,
                    "workflow_name": workflow_name,
                    "outcome": event.event_type.value,
                    "reason": str(getattr(event, "reason", "")),
                    "timestamp": event.timestamp.isoformat(),
                }
            )

        if event.event_type in {
            EventType.ORCHESTRATION_DELIVERY_ATTEMPTED,
            EventType.ORCHESTRATION_DELIVERY_SUCCEEDED,
            EventType.ORCHESTRATION_DELIVERY_FAILED,
        }:
            delivery_outcomes.append(
                {
                    "run_id": run_id,
                    "workflow_name": workflow_name,
                    "outcome": event.event_type.value,
                    "reminder_type": str(getattr(event, "reminder_type", "")),
                    "delivery_channel": str(getattr(event, "delivery_channel", "")),
                    "timestamp": event.timestamp.isoformat(),
                }
            )

    recent_runs = sorted(
        run_status.values(),
        key=lambda item: item.get("started_at", ""),
        reverse=True,
    )[:limit]

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "runs": recent_runs,
        "policy_outcomes": policy_outcomes[-limit:],
        "delivery_outcomes": delivery_outcomes[-limit:],
    }


@router.get("/overview", response_model=ControlRoomOverview)
async def get_control_room_overview(
    services: tuple[Config, AttentionService] = Depends(get_control_room_services),
) -> ControlRoomOverview:
    """Return consolidated read-only operator transparency payload."""
    config, attention_service = services

    readiness = _readiness_from_config(config)
    today = await attention_service.get_today_attention(limit=10)
    week = await attention_service.get_week_attention()
    orchestration = await _orchestration_visibility(config=config, limit=25)

    return ControlRoomOverview(
        health={"status": "healthy", "service": "helionyx"},
        readiness=readiness,
        attention_today=today,
        attention_week=week,
        orchestration=orchestration,
        generated_at=datetime.utcnow().isoformat(),
    )


@router.get("/orchestration", response_model=dict)
async def get_orchestration_visibility() -> dict:
    """Return orchestration run/node/policy/delivery visibility summary."""
    config = Config.from_env()
    return await _orchestration_visibility(config=config, limit=50)


@router.post("/orchestration/run", response_model=dict)
async def run_orchestration_workflow(
    workflow_name: str = Query(..., description="daily_digest|weekly_digest|urgent_reminder"),
    dry_run: bool = Query(True),
) -> dict:
    """Trigger a single orchestration workflow run via API through shared runtime boundary."""
    config = Config.from_env()
    event_store = FileEventStore(data_dir=config.EVENT_STORE_PATH)
    query_service = QueryService(event_store, db_path=Path(config.PROJECTIONS_DB_PATH))
    try:
        telegram_scheduler.config = config
        telegram_scheduler.event_store = event_store
        telegram_scheduler.query_service = query_service
        telegram_scheduler.db_conn = query_service.conn
        return await telegram_scheduler.run_orchestration_workflow(
            bot=None,
            workflow_name=workflow_name,
            dry_run=dry_run,
        )
    finally:
        query_service.close()
