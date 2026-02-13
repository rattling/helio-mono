"""Data Explorer API endpoints (Milestone 10)."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from shared.common.config import Config
from shared.contracts import (
    AttentionScoringComputedEvent,
    BaseEvent,
    DecisionRecordedEvent,
    ExplorerDecisionEvidenceResponse,
    ExplorerEntityType,
    ExplorerIdentifierRef,
    ExplorerLookupResponse,
    ExplorerStateSnapshotResponse,
    ExplorerTimelineEvent,
    ExplorerTimelineResponse,
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
