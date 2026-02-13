"""Data Explorer API endpoints (Milestone 10)."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from shared.common.config import Config
from shared.contracts import (
    AttentionScoringComputedEvent,
    BaseEvent,
    DecisionRecordedEvent,
    ExplorerDecisionEvidenceResponse,
    ExplorerEvidenceRef,
    ExplorerEntityType,
    ExplorerGuidedInsightsResponse,
    ExplorerIdentifierRef,
    ExplorerLookupResponse,
    ExplorerNotableEvent,
    ExplorerPulse,
    ExplorerPulseMetric,
    ExplorerRankingFactor,
    ExplorerRankingMetadata,
    ExplorerStateSnapshotResponse,
    ExplorerTimelineEvent,
    ExplorerTimelineResponse,
    ExplorerViewMode,
    NotableSeverity,
)
from services.event_store.file_store import FileEventStore
from services.query.service import QueryService

router = APIRouter()


def get_explorer_services() -> Generator[tuple[FileEventStore, QueryService], None, None]:
    """Get initialized explorer dependencies."""
    config = Config.from_env()
    event_store = FileEventStore(data_dir=config.EVENT_STORE_PATH)
    query_service = QueryService(event_store, db_path=Path(config.PROJECTIONS_DB_PATH))
    try:
        yield event_store, query_service
    finally:
        query_service.close()


def _event_links(event: BaseEvent) -> list[ExplorerIdentifierRef]:
    links: list[ExplorerIdentifierRef] = []

    task_id = getattr(event, "task_id", None)
    if task_id:
        links.append(
            ExplorerIdentifierRef(
                entity_type=ExplorerEntityType.TASK,
                entity_id=str(task_id),
                relation="task_id",
            )
        )

    object_id = getattr(event, "object_id", None)
    if object_id:
        links.append(
            ExplorerIdentifierRef(
                entity_type=ExplorerEntityType.TASK,
                entity_id=str(object_id),
                relation="object_id",
            )
        )

    candidate_id = getattr(event, "candidate_id", None)
    if candidate_id:
        links.append(
            ExplorerIdentifierRef(
                entity_type=ExplorerEntityType.TASK,
                entity_id=str(candidate_id),
                relation="candidate_id",
            )
        )

    if isinstance(event, DecisionRecordedEvent):
        decision_task_id = (event.decision_data or {}).get("task_snapshot", {}).get("task_id")
        if decision_task_id:
            links.append(
                ExplorerIdentifierRef(
                    entity_type=ExplorerEntityType.TASK,
                    entity_id=str(decision_task_id),
                    relation="decision.task_snapshot.task_id",
                )
            )

    if isinstance(event, AttentionScoringComputedEvent):
        for candidate in event.candidates:
            links.append(
                ExplorerIdentifierRef(
                    entity_type=ExplorerEntityType.TASK,
                    entity_id=str(candidate.task_id),
                    relation="attention_candidate",
                )
            )

    return links


def _matches_task(event: BaseEvent, task_id: str) -> bool:
    if str(getattr(event, "task_id", "")) == task_id:
        return True
    if str(getattr(event, "object_id", "")) == task_id:
        return True
    if str(getattr(event, "candidate_id", "")) == task_id:
        return True

    if isinstance(event, DecisionRecordedEvent):
        decision_task_id = (event.decision_data or {}).get("task_snapshot", {}).get("task_id")
        if str(decision_task_id) == task_id:
            return True

    if isinstance(event, AttentionScoringComputedEvent):
        return any(str(candidate.task_id) == task_id for candidate in event.candidates)

    return False


def _timeline_event(event: BaseEvent) -> ExplorerTimelineEvent:
    return ExplorerTimelineEvent(
        event_id=str(event.event_id),
        event_type=event.event_type.value,
        timestamp=event.timestamp,
        rationale=getattr(event, "rationale", None),
        links=_event_links(event),
        payload=event.model_dump(mode="json"),
    )


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _severity_and_base_score(event_type: str) -> tuple[NotableSeverity, float]:
    event_type = event_type.lower()
    if "failed" in event_type:
        return NotableSeverity.CRITICAL, 4.0
    if "rejected" in event_type:
        return NotableSeverity.RISK, 3.6
    if "dismissed" in event_type or "snoozed" in event_type:
        return NotableSeverity.WARNING, 2.7
    if "decision" in event_type or "suggestion" in event_type or "reminder" in event_type:
        return NotableSeverity.INFO, 2.2
    return NotableSeverity.INFO, 1.4


def _severity_rank(severity: NotableSeverity) -> int:
    return {
        NotableSeverity.CRITICAL: 4,
        NotableSeverity.RISK: 3,
        NotableSeverity.WARNING: 2,
        NotableSeverity.INFO: 1,
    }[severity]


def _event_title(event_type: str) -> str:
    return event_type.replace("_", " ").strip().title()


def _make_evidence_refs(
    event: BaseEvent, links: list[ExplorerIdentifierRef]
) -> list[ExplorerEvidenceRef]:
    refs: list[ExplorerEvidenceRef] = []
    first_link = links[0] if links else None
    if first_link:
        refs.append(
            ExplorerEvidenceRef(
                view=ExplorerViewMode.TIMELINE,
                entity_type=first_link.entity_type,
                entity_id=first_link.entity_id,
                reason="Inspect full timeline context",
            )
        )
        refs.append(
            ExplorerEvidenceRef(
                view=ExplorerViewMode.DECISION,
                entity_type=first_link.entity_type,
                entity_id=first_link.entity_id,
                reason="Inspect decision-oriented evidence",
            )
        )
    refs.append(
        ExplorerEvidenceRef(
            view=ExplorerViewMode.TIMELINE,
            entity_type=ExplorerEntityType.EVENT,
            entity_id=str(event.event_id),
            reason="Inspect source event payload",
        )
    )
    return refs


def _score_notable(event: BaseEvent, now: datetime) -> ExplorerNotableEvent:
    links = _event_links(event)
    severity, severity_score = _severity_and_base_score(event.event_type.value)
    age_hours = max(0.0, (now - event.timestamp.replace(tzinfo=None)).total_seconds() / 3600)
    recency_score = max(0.0, 3.0 - (age_hours / 12.0))
    blast_radius_score = min(2.0, len({(item.entity_type, item.entity_id) for item in links}) * 0.5)
    novelty_score = (
        1.2
        if ("rejected" in event.event_type.value or "dismissed" in event.event_type.value)
        else 0.4
    )
    relevance_score = (
        1.0
        if any(
            marker in event.event_type.value
            for marker in ("decision", "suggestion", "reminder", "attention")
        )
        else 0.5
    )

    factors = [
        ExplorerRankingFactor(key="severity", label="Severity", value=severity_score),
        ExplorerRankingFactor(key="recency", label="Recency", value=recency_score),
        ExplorerRankingFactor(key="blast_radius", label="Blast Radius", value=blast_radius_score),
        ExplorerRankingFactor(key="novelty", label="Novelty/Regression", value=novelty_score),
        ExplorerRankingFactor(
            key="operator_relevance", label="Operator Relevance", value=relevance_score
        ),
    ]
    composite_score = round(sum(item.value for item in factors), 4)

    summary = getattr(event, "rationale", None) or "Inspect evidence links for full context."

    return ExplorerNotableEvent(
        notable_id=f"{event.event_id}:{event.event_type.value}",
        title=_event_title(event.event_type.value),
        summary=summary,
        event_type=event.event_type.value,
        event_id=str(event.event_id),
        timestamp=event.timestamp,
        ranking=ExplorerRankingMetadata(
            severity=severity,
            composite_score=composite_score,
            factors=factors,
        ),
        evidence_refs=_make_evidence_refs(event, links),
    )


def _pulse_status(value: int, high: int, medium: int) -> str:
    if value >= high:
        return "high"
    if value >= medium:
        return "elevated"
    return "normal"


async def _collect_timeline(
    event_store: FileEventStore,
    entity_type: ExplorerEntityType,
    entity_id: str,
    since: datetime | None,
    until: datetime | None,
    limit: int,
) -> list[ExplorerTimelineEvent]:
    events = await event_store.stream_events(since=since)
    filtered: list[BaseEvent] = []

    for event in events:
        if until and event.timestamp > until:
            continue

        if entity_type == ExplorerEntityType.EVENT:
            if str(event.event_id) == entity_id:
                filtered.append(event)
        elif entity_type == ExplorerEntityType.TASK:
            if _matches_task(event, entity_id):
                filtered.append(event)

    filtered.sort(key=lambda item: item.timestamp)
    return [_timeline_event(item) for item in filtered[:limit]]


@router.get("/lookup", response_model=ExplorerLookupResponse)
async def explorer_lookup(
    entity_type: ExplorerEntityType = Query(...),
    entity_id: str = Query(...),
    services: tuple[FileEventStore, QueryService] = Depends(get_explorer_services),
) -> ExplorerLookupResponse:
    """Lookup canonical entity data by type/id."""
    event_store, query_service = services

    if entity_type == ExplorerEntityType.TASK:
        task = await query_service.get_task_by_id(entity_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        related = [
            ExplorerIdentifierRef(
                entity_type=ExplorerEntityType.TASK,
                entity_id=str(item),
                relation="blocked_by",
            )
            for item in task.get("blocked_by", [])
        ]

        return ExplorerLookupResponse(
            entity_type=entity_type,
            entity_id=entity_id,
            canonical=task,
            related_identifiers=related,
        )

    if entity_type == ExplorerEntityType.EVENT:
        try:
            event_uuid = UUID(entity_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="entity_id must be a valid UUID for event lookup",
            ) from exc

        event = await event_store.get_by_id(event_uuid)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

        return ExplorerLookupResponse(
            entity_type=entity_type,
            entity_id=entity_id,
            canonical=event.model_dump(mode="json"),
            related_identifiers=_event_links(event),
        )

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported entity_type")


@router.get("/timeline", response_model=ExplorerTimelineResponse)
async def explorer_timeline(
    entity_type: ExplorerEntityType = Query(...),
    entity_id: str = Query(...),
    since: datetime | None = Query(None),
    until: datetime | None = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    services: tuple[FileEventStore, QueryService] = Depends(get_explorer_services),
) -> ExplorerTimelineResponse:
    """Return ordered event timeline for an entity context."""
    event_store, _ = services
    timeline = await _collect_timeline(event_store, entity_type, entity_id, since, until, limit)
    return ExplorerTimelineResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        events=timeline,
        since=since,
        until=until,
    )


@router.get("/state", response_model=ExplorerStateSnapshotResponse)
async def explorer_state(
    entity_type: ExplorerEntityType = Query(...),
    entity_id: str = Query(...),
    services: tuple[FileEventStore, QueryService] = Depends(get_explorer_services),
) -> ExplorerStateSnapshotResponse:
    """Return current projection/state snapshot plus traceability references."""
    event_store, query_service = services

    if entity_type != ExplorerEntityType.TASK:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State snapshot currently supports entity_type=task",
        )

    task = await query_service.get_task_by_id(entity_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    timeline = await _collect_timeline(event_store, entity_type, entity_id, None, None, 1000)
    event_ids = [item.event_id for item in timeline]

    return ExplorerStateSnapshotResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        snapshot=task,
        traceability={
            "event_count": len(event_ids),
            "event_ids": event_ids,
            "latest_event_id": event_ids[-1] if event_ids else None,
        },
    )


@router.get("/decision", response_model=ExplorerDecisionEvidenceResponse)
async def explorer_decision(
    entity_type: ExplorerEntityType = Query(...),
    entity_id: str = Query(...),
    since: datetime | None = Query(None),
    until: datetime | None = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    services: tuple[FileEventStore, QueryService] = Depends(get_explorer_services),
) -> ExplorerDecisionEvidenceResponse:
    """Return decision/rationale oriented evidence for an entity context."""
    event_store, _ = services
    timeline = await _collect_timeline(event_store, entity_type, entity_id, since, until, limit)
    decision_like = [
        item
        for item in timeline
        if "decision" in item.event_type
        or "suggestion" in item.event_type
        or "reminder" in item.event_type
    ]
    return ExplorerDecisionEvidenceResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        decisions=decision_like,
    )


@router.get("/insights", response_model=ExplorerGuidedInsightsResponse)
async def explorer_insights(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(15, ge=1, le=100),
    services: tuple[FileEventStore, QueryService] = Depends(get_explorer_services),
) -> ExplorerGuidedInsightsResponse:
    """Return guided-insights pulse and deterministic notable-events feed."""
    event_store, query_service = services

    now = datetime.utcnow()
    since = now - timedelta(days=days)
    events = await event_store.stream_events(since=since)
    events = sorted(events, key=lambda item: item.timestamp, reverse=True)

    all_tasks = await query_service.get_tasks(limit=500)
    open_tasks = [task for task in all_tasks if task.get("status") not in {"done", "cancelled"}]
    blocked_tasks = [task for task in open_tasks if (task.get("blocked_by") or [])]
    overdue_tasks = [
        task
        for task in open_tasks
        if (due_at := _parse_datetime(task.get("due_at"))) and due_at < now
    ]
    stale_tasks = [
        task
        for task in open_tasks
        if (updated_at := _parse_datetime(task.get("updated_at")))
        and updated_at < (now - timedelta(days=7))
    ]

    recent_events_24h = [
        event
        for event in events
        if event.timestamp.replace(tzinfo=None) >= now - timedelta(hours=24)
    ]

    pulse = ExplorerPulse(
        generated_at=now,
        metrics=[
            ExplorerPulseMetric(
                key="open_tasks",
                label="Open Tasks",
                value=len(open_tasks),
                status=_pulse_status(len(open_tasks), high=25, medium=10),
                description="Tasks not in done/cancelled state",
            ),
            ExplorerPulseMetric(
                key="blocked_tasks",
                label="Blocked Tasks",
                value=len(blocked_tasks),
                status=_pulse_status(len(blocked_tasks), high=8, medium=3),
                description="Open tasks with dependency blockers",
            ),
            ExplorerPulseMetric(
                key="overdue_tasks",
                label="Overdue Tasks",
                value=len(overdue_tasks),
                status=_pulse_status(len(overdue_tasks), high=5, medium=1),
                description="Open tasks with due_at before now",
            ),
            ExplorerPulseMetric(
                key="stale_tasks",
                label="Stale Tasks",
                value=len(stale_tasks),
                status=_pulse_status(len(stale_tasks), high=10, medium=4),
                description="Open tasks not updated in the last 7 days",
            ),
            ExplorerPulseMetric(
                key="events_24h",
                label="Events (24h)",
                value=len(recent_events_24h),
                status=_pulse_status(len(recent_events_24h), high=100, medium=30),
                description="Event throughput in the last 24 hours",
            ),
        ],
    )

    candidates = [_score_notable(event, now) for event in events]
    candidates.sort(
        key=lambda item: (
            _severity_rank(item.ranking.severity),
            item.ranking.composite_score,
            item.timestamp,
            item.event_id,
        ),
        reverse=True,
    )

    return ExplorerGuidedInsightsResponse(
        generated_at=now,
        pulse=pulse,
        notable_events=candidates[:limit],
    )
