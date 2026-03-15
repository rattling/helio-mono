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


def _default_run_summary(*, run_id: str, workflow_name: str) -> dict:
    return {
        "run_id": run_id,
        "workflow_name": workflow_name,
        "status": "in_progress",
        "checkpoints": [],
        "latest_checkpoint": None,
        "interrupt": None,
        "resume": {
            "eligible": False,
            "supported": True,
            "pending": False,
            "last_decision": None,
            "action": {
                "method": "POST",
                "path": "/api/v1/control-room/orchestration/resume",
                "required_fields": ["run_id", "resume_value"],
            },
        },
        "delivery": {
            "planned_channels": [],
            "attempted_channels": [],
            "succeeded_channels": [],
            "failed_channels": [],
            "pending_channels": [],
        },
        "degraded": False,
        "degraded_reasons": [],
        "partial_delivery": False,
    }


def _ensure_run(run_status: dict[str, dict], *, run_id: str, workflow_name: str) -> dict:
    existing = run_status.get(run_id)
    if existing:
        if workflow_name and not existing.get("workflow_name"):
            existing["workflow_name"] = workflow_name
        return existing

    run = _default_run_summary(run_id=run_id, workflow_name=workflow_name)
    run_status[run_id] = run
    return run


def _append_unique(target: list[str], values: list[str]) -> None:
    for value in values:
        if value and value not in target:
            target.append(value)


def _mark_degraded(run: dict, reason: str) -> None:
    run["degraded"] = True
    if reason not in run["degraded_reasons"]:
        run["degraded_reasons"].append(reason)


def _apply_output_degradation(run: dict, payload: dict) -> None:
    if not payload:
        return

    delivery = run["delivery"]
    _append_unique(delivery["succeeded_channels"], list(payload.get("sent_channels") or []))
    _append_unique(delivery["failed_channels"], list(payload.get("failed_channels") or []))

    calendar_status = payload.get("calendar_status") or {}
    if payload.get("calendar_degraded"):
        _mark_degraded(run, "calendar_provider_degraded")
    for provider, status in calendar_status.items():
        if status != "ok":
            _mark_degraded(run, f"calendar:{provider}:{status}")

    if payload.get("partial_success"):
        run["partial_delivery"] = True
        _mark_degraded(run, "partial_delivery")

    channel_results = payload.get("channel_results") or []
    if any(not item.get("sent") for item in channel_results):
        _mark_degraded(run, "delivery_channel_failure")


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
        run = _ensure_run(run_status, run_id=run_id, workflow_name=workflow_name)

        if event.event_type == EventType.ORCHESTRATION_RUN_STARTED:
            run["started_at"] = event.timestamp.isoformat()
            run["status"] = "in_progress"
            run["trigger"] = str(getattr(event, "trigger", ""))
            run["metadata"] = getattr(event, "metadata", {})
        elif event.event_type == EventType.ORCHESTRATION_RUN_CHECKPOINT:
            checkpoint = str(getattr(event, "checkpoint", ""))
            details = getattr(event, "details", {})
            checkpoint_payload = {
                "checkpoint": checkpoint,
                "timestamp": event.timestamp.isoformat(),
                "details": details,
            }
            run["checkpoints"].append(checkpoint_payload)
            run["latest_checkpoint"] = checkpoint_payload

            if checkpoint == "interrupt_requested":
                run["status"] = "interrupted"
                run["reason"] = str(details.get("reason") or run.get("reason") or "interrupted")
                run["interrupt"] = {
                    "pending": True,
                    "requested_at": event.timestamp.isoformat(),
                    "resumed_at": None,
                    "reason": str(details.get("reason") or "manual_approval_required"),
                    "details": details,
                }
                run["resume"] = {
                    "eligible": True,
                    "supported": True,
                    "pending": True,
                    "last_decision": None,
                    "action": {
                        "method": "POST",
                        "path": "/api/v1/control-room/orchestration/resume",
                        "required_fields": ["run_id", "resume_value"],
                        "run_id": run_id,
                    },
                }
            elif checkpoint == "interrupt_resumed":
                interrupt_payload = run.get("interrupt") or {}
                interrupt_payload["pending"] = False
                interrupt_payload["resumed_at"] = event.timestamp.isoformat()
                run["interrupt"] = interrupt_payload
                run["resume"]["eligible"] = False
                run["resume"]["pending"] = False
                run["resume"]["last_decision"] = details
                if run.get("status") == "interrupted":
                    run["status"] = "in_progress"
            elif checkpoint == "delivery_attempt":
                planned_channels = [
                    str(value)
                    for value in list(details.get("planned_channels") or [])
                    if str(value)
                ]
                if not planned_channels:
                    single_channel = str(details.get("delivery_channel") or "")
                    planned_channels = [single_channel] if single_channel else []
                _append_unique(run["delivery"]["planned_channels"], planned_channels)
        elif event.event_type == EventType.ORCHESTRATION_RUN_FINISHED:
            run["status"] = "completed"
            run["finished_at"] = event.timestamp.isoformat()
            run["output"] = getattr(event, "output", {})
            _apply_output_degradation(run, run["output"])
        elif event.event_type == EventType.ORCHESTRATION_RUN_FAILED:
            run["status"] = "failed"
            run["finished_at"] = event.timestamp.isoformat()
            run["reason"] = str(getattr(event, "reason", "unknown"))
            run["details"] = getattr(event, "details", {})
            _apply_output_degradation(run, run["details"])

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
            run["policy"] = {
                "outcome": event.event_type.value,
                "reason": str(getattr(event, "reason", "")),
                "timestamp": event.timestamp.isoformat(),
            }

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
                    "reason": str(getattr(event, "reason", "")),
                    "details": getattr(event, "details", {}),
                    "timestamp": event.timestamp.isoformat(),
                }
            )
            delivery_channel = str(getattr(event, "delivery_channel", ""))
            if event.event_type == EventType.ORCHESTRATION_DELIVERY_ATTEMPTED:
                _append_unique(run["delivery"]["attempted_channels"], [delivery_channel])
            elif event.event_type == EventType.ORCHESTRATION_DELIVERY_SUCCEEDED:
                _append_unique(run["delivery"]["succeeded_channels"], [delivery_channel])
            elif event.event_type == EventType.ORCHESTRATION_DELIVERY_FAILED:
                _append_unique(run["delivery"]["failed_channels"], [delivery_channel])
                _mark_degraded(run, "delivery_channel_failure")

    for run in run_status.values():
        pending_channels = [
            channel
            for channel in run["delivery"]["planned_channels"]
            if channel
            and channel not in run["delivery"]["succeeded_channels"]
            and channel not in run["delivery"]["failed_channels"]
        ]
        run["delivery"]["pending_channels"] = pending_channels
        if run["delivery"]["succeeded_channels"] and run["delivery"]["failed_channels"]:
            run["partial_delivery"] = True
            _mark_degraded(run, "partial_delivery")

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
        "summary": {
            "interrupted_runs": sum(
                1 for item in recent_runs if item.get("status") == "interrupted"
            ),
            "degraded_runs": sum(1 for item in recent_runs if item.get("degraded")),
            "partial_delivery_runs": sum(1 for item in recent_runs if item.get("partial_delivery")),
        },
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
