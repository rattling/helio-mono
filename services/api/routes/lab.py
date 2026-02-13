"""Lab API endpoints (Milestone 11)."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from shared.common.config import Config
from shared.contracts import (
    EventType,
    LabConfigSnapshot,
    LabControlChangedEvent,
    LabControlUpdateRequest,
    LabControlUpdateResponse,
    LabDiagnosticMetric,
    LabDiagnostics,
    LabExperimentAppliedEvent,
    LabExperimentApplyRequest,
    LabExperimentHistoryItem,
    LabExperimentHistoryResponse,
    LabExperimentRunEvent,
    LabExperimentRunRequest,
    LabExperimentRunResult,
    LabOverviewResponse,
    LabPersonalizationMode,
    LabRollbackRequest,
)
from services.event_store.file_store import FileEventStore
from services.query.service import QueryService

router = APIRouter()


def get_lab_services() -> Generator[tuple[FileEventStore, QueryService, Config], None, None]:
    config = Config.from_env()
    event_store = FileEventStore(data_dir=config.EVENT_STORE_PATH)
    query_service = QueryService(event_store, db_path=Path(config.PROJECTIONS_DB_PATH))
    try:
        yield event_store, query_service, config
    finally:
        query_service.close()


def _base_config_snapshot(config: Config) -> LabConfigSnapshot:
    return LabConfigSnapshot(
        mode=LabPersonalizationMode(config.ATTENTION_PERSONALIZATION_MODE),
        shadow_ranker_enabled=config.SHADOW_RANKER_ENABLED,
        bounded_personalization_enabled=config.ATTENTION_BOUNDED_PERSONALIZATION_ENABLED,
        shadow_confidence_threshold=config.SHADOW_RANKER_CONFIDENCE_THRESHOLD,
    )


def _to_snapshot(state: dict) -> LabConfigSnapshot:
    mode = LabPersonalizationMode(state.get("mode", "deterministic"))
    return LabConfigSnapshot(
        mode=mode,
        shadow_ranker_enabled=mode
        in (
            LabPersonalizationMode.SHADOW,
            LabPersonalizationMode.BOUNDED,
        ),
        bounded_personalization_enabled=mode == LabPersonalizationMode.BOUNDED,
        shadow_confidence_threshold=float(state.get("shadow_confidence_threshold", 0.6)),
    )


async def _effective_config(event_store: FileEventStore, config: Config) -> LabConfigSnapshot:
    base = _base_config_snapshot(config)
    events = await event_store.stream_events(event_types=[EventType.LAB_CONTROL_CHANGED])
    if not events:
        return base
    latest = max(events, key=lambda item: item.timestamp)
    if not isinstance(latest, LabControlChangedEvent):
        return base
    merged = {
        "mode": base.mode.value,
        "shadow_confidence_threshold": base.shadow_confidence_threshold,
    }
    merged.update(latest.after)
    return _to_snapshot(merged)


async def _diagnostics(event_store: FileEventStore, query_service: QueryService) -> LabDiagnostics:
    now = datetime.utcnow()
    tasks = await query_service.get_tasks(limit=500)
    open_tasks = [item for item in tasks if item.get("status") not in {"done", "cancelled"}]

    model_events = await event_store.get_by_type(
        EventType.MODEL_SCORE_RECORDED,
        since=now - timedelta(days=7),
    )
    feedback_events = await event_store.get_by_type(
        EventType.FEEDBACK_EVIDENCE_RECORDED,
        since=now - timedelta(days=7),
    )

    high_conf = [
        item for item in model_events if float(getattr(item, "confidence", 0.0) or 0.0) >= 0.7
    ]
    low_conf = [
        item for item in model_events if float(getattr(item, "confidence", 0.0) or 0.0) < 0.5
    ]

    metrics = [
        LabDiagnosticMetric(
            key="open_tasks",
            label="Open Tasks",
            value=len(open_tasks),
            status="normal" if len(open_tasks) < 30 else "elevated",
            description="Tasks not in done/cancelled state",
        ),
        LabDiagnosticMetric(
            key="model_scores_7d",
            label="Model Scores (7d)",
            value=len(model_events),
            status="normal" if model_events else "low",
            description="Recorded model score events",
        ),
        LabDiagnosticMetric(
            key="high_confidence_7d",
            label="High Confidence Scores",
            value=len(high_conf),
            status="normal",
            description="Model scores with confidence >= 0.70",
        ),
        LabDiagnosticMetric(
            key="low_confidence_7d",
            label="Low Confidence Scores",
            value=len(low_conf),
            status="risk" if low_conf else "normal",
            description="Model scores with confidence < 0.50",
        ),
        LabDiagnosticMetric(
            key="feedback_events_7d",
            label="Feedback Evidence (7d)",
            value=len(feedback_events),
            status="normal" if feedback_events else "low",
            description="Weak-label feedback evidence events",
        ),
    ]
    return LabDiagnostics(generated_at=now, metrics=metrics)


@router.get("/overview", response_model=LabOverviewResponse)
async def lab_overview(
    services: tuple[FileEventStore, QueryService, Config] = Depends(get_lab_services),
) -> LabOverviewResponse:
    event_store, query_service, config = services
    effective = await _effective_config(event_store, config)
    diagnostics = await _diagnostics(event_store, query_service)
    return LabOverviewResponse(
        generated_at=datetime.utcnow(),
        diagnostics=diagnostics,
        config=effective,
        fallback_state={
            "deterministic_fallback_active": effective.mode == LabPersonalizationMode.DETERMINISTIC,
            "safety_reason": "deterministic baseline is always available",
        },
    )


@router.post("/controls", response_model=LabControlUpdateResponse)
async def lab_update_controls(
    request: LabControlUpdateRequest,
    services: tuple[FileEventStore, QueryService, Config] = Depends(get_lab_services),
) -> LabControlUpdateResponse:
    event_store, _, config = services
    before = await _effective_config(event_store, config)

    after = {
        "mode": request.mode.value,
        "shadow_confidence_threshold": request.shadow_confidence_threshold,
    }

    rollback_to = {
        "mode": LabPersonalizationMode.DETERMINISTIC.value,
        "shadow_confidence_threshold": 0.6,
    }

    event = LabControlChangedEvent(
        actor=request.actor,
        rationale=request.rationale,
        before={
            "mode": before.mode.value,
            "shadow_confidence_threshold": before.shadow_confidence_threshold,
        },
        after=after,
        rollback_to=rollback_to,
        metadata={"service": "lab_api"},
    )
    await event_store.append(event)

    return LabControlUpdateResponse(
        status="updated",
        effective_config=_to_snapshot(after),
        audit={
            "event_id": str(event.event_id),
            "actor": request.actor,
            "rationale": request.rationale,
        },
    )


@router.post("/rollback", response_model=LabControlUpdateResponse)
async def lab_rollback(
    request: LabRollbackRequest,
    services: tuple[FileEventStore, QueryService, Config] = Depends(get_lab_services),
) -> LabControlUpdateResponse:
    event_store, _, config = services
    before = await _effective_config(event_store, config)
    after = {
        "mode": LabPersonalizationMode.DETERMINISTIC.value,
        "shadow_confidence_threshold": 0.6,
    }

    event = LabControlChangedEvent(
        actor=request.actor,
        rationale=request.rationale,
        before={
            "mode": before.mode.value,
            "shadow_confidence_threshold": before.shadow_confidence_threshold,
        },
        after=after,
        rollback_to=after,
        metadata={"service": "lab_api", "action": "rollback"},
    )
    await event_store.append(event)

    return LabControlUpdateResponse(
        status="rolled_back",
        effective_config=_to_snapshot(after),
        audit={
            "event_id": str(event.event_id),
            "actor": request.actor,
            "rationale": request.rationale,
            "action": "rollback",
        },
    )


@router.post("/experiments/run", response_model=LabExperimentRunResult)
async def run_experiment(
    request: LabExperimentRunRequest,
    services: tuple[FileEventStore, QueryService, Config] = Depends(get_lab_services),
) -> LabExperimentRunResult:
    event_store, _, config = services
    baseline = await _effective_config(event_store, config)
    now = datetime.utcnow()

    candidate = {
        "mode": request.candidate_mode.value,
        "shadow_confidence_threshold": request.candidate_shadow_confidence_threshold,
    }
    baseline_payload = {
        "mode": baseline.mode.value,
        "shadow_confidence_threshold": baseline.shadow_confidence_threshold,
    }

    improvement = 0.0
    if request.candidate_mode == LabPersonalizationMode.BOUNDED:
        improvement += 0.15
    elif request.candidate_mode == LabPersonalizationMode.SHADOW:
        improvement += 0.07

    improvement += max(0.0, 0.75 - request.candidate_shadow_confidence_threshold) * 0.1

    apply_allowed = request.candidate_shadow_confidence_threshold >= 0.4
    block_reason = (
        None if apply_allowed else "candidate_shadow_confidence_threshold below safety floor"
    )

    run_id = str(uuid4())
    comparison = {
        "estimated_attention_quality_delta": round(improvement, 4),
        "safety_gate": "pass" if apply_allowed else "blocked",
    }

    run_event = LabExperimentRunEvent(
        run_id=run_id,
        actor=request.actor,
        experiment_type=request.experiment_type,
        candidate_config=candidate,
        baseline_config=baseline_payload,
        result={
            "comparison": comparison,
            "apply_allowed": apply_allowed,
            "apply_block_reason": block_reason,
            "rationale": request.rationale,
        },
        metadata={"service": "lab_api"},
    )
    await event_store.append(run_event)

    return LabExperimentRunResult(
        run_id=run_id,
        status="completed",
        generated_at=now,
        baseline=baseline_payload,
        candidate=candidate,
        comparison=comparison,
        apply_allowed=apply_allowed,
        apply_block_reason=block_reason,
    )


@router.get("/experiments/history", response_model=LabExperimentHistoryResponse)
async def experiment_history(
    limit: int = Query(20, ge=1, le=100),
    services: tuple[FileEventStore, QueryService, Config] = Depends(get_lab_services),
) -> LabExperimentHistoryResponse:
    event_store, _, _ = services
    events = await event_store.stream_events(event_types=[EventType.LAB_EXPERIMENT_RUN])
    run_events = [item for item in events if isinstance(item, LabExperimentRunEvent)]
    run_events.sort(key=lambda item: item.timestamp, reverse=True)

    return LabExperimentHistoryResponse(
        runs=[
            LabExperimentHistoryItem(
                run_id=item.run_id,
                generated_at=item.timestamp,
                actor=item.actor,
                experiment_type=item.experiment_type,
                candidate=item.candidate_config,
                apply_allowed=bool(item.result.get("apply_allowed")),
                status="completed",
            )
            for item in run_events[:limit]
        ]
    )


@router.post("/experiments/{run_id}/apply", response_model=LabControlUpdateResponse)
async def apply_experiment(
    run_id: str,
    request: LabExperimentApplyRequest,
    services: tuple[FileEventStore, QueryService, Config] = Depends(get_lab_services),
) -> LabControlUpdateResponse:
    event_store, _, config = services

    run_events = await event_store.stream_events(event_types=[EventType.LAB_EXPERIMENT_RUN])
    target = next(
        (
            item
            for item in run_events
            if isinstance(item, LabExperimentRunEvent) and item.run_id == run_id
        ),
        None,
    )
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment run not found"
        )

    apply_allowed = bool(target.result.get("apply_allowed"))
    if request.action == "apply" and not apply_allowed:
        reason = target.result.get("apply_block_reason") or "safety gate blocked apply"
        rejection = LabExperimentAppliedEvent(
            run_id=run_id,
            actor=request.actor,
            rationale=request.rationale,
            action=request.action,
            applied=False,
            reason=reason,
            metadata={"service": "lab_api"},
        )
        await event_store.append(rejection)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=reason)

    before = await _effective_config(event_store, config)
    if request.action == "apply":
        after_state = {
            "mode": target.candidate_config.get("mode", before.mode.value),
            "shadow_confidence_threshold": float(
                target.candidate_config.get(
                    "shadow_confidence_threshold", before.shadow_confidence_threshold
                )
            ),
        }
        status_text = "updated"
    elif request.action == "rollback":
        after_state = {
            "mode": LabPersonalizationMode.DETERMINISTIC.value,
            "shadow_confidence_threshold": 0.6,
        }
        status_text = "rolled_back"
    else:
        after_state = {
            "mode": before.mode.value,
            "shadow_confidence_threshold": before.shadow_confidence_threshold,
        }
        status_text = "no_op"

    apply_event = LabExperimentAppliedEvent(
        run_id=run_id,
        actor=request.actor,
        rationale=request.rationale,
        action=request.action,
        applied=request.action != "no_op",
        metadata={"service": "lab_api"},
    )
    await event_store.append(apply_event)

    control_event = LabControlChangedEvent(
        actor=request.actor,
        rationale=f"experiment:{run_id}:{request.rationale}",
        before={
            "mode": before.mode.value,
            "shadow_confidence_threshold": before.shadow_confidence_threshold,
        },
        after=after_state,
        rollback_to={
            "mode": LabPersonalizationMode.DETERMINISTIC.value,
            "shadow_confidence_threshold": 0.6,
        },
        metadata={"service": "lab_api", "source": "experiment_apply"},
    )
    await event_store.append(control_event)

    return LabControlUpdateResponse(
        status=status_text,
        effective_config=_to_snapshot(after_state),
        audit={
            "event_id": str(control_event.event_id),
            "run_id": run_id,
            "action": request.action,
            "actor": request.actor,
        },
    )
