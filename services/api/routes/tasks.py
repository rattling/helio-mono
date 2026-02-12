"""Task API endpoints (Milestone 5)."""

from pathlib import Path
from collections.abc import Generator
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from shared.common.config import Config
from shared.contracts import (
    TaskApplySuggestionRequest,
    TaskIngestRequest,
    TaskIngestResult,
    TaskLinkRequest,
    TaskPatchRequest,
    TaskRejectSuggestionRequest,
    TaskSnoozeRequest,
)
from services.event_store.file_store import FileEventStore
from services.query.service import QueryService
from services.task.service import TaskService

router = APIRouter()


def get_task_service() -> Generator[TaskService, None, None]:
    """Get initialized task service."""
    config = Config.from_env()
    event_store = FileEventStore(data_dir=config.EVENT_STORE_PATH)
    query_service = QueryService(event_store, db_path=Path(config.PROJECTIONS_DB_PATH))
    try:
        yield TaskService(event_store=event_store, query_service=query_service)
    finally:
        query_service.close()


@router.post("/ingest", response_model=TaskIngestResult, status_code=status.HTTP_201_CREATED)
async def ingest_task(
    request: TaskIngestRequest,
    task_service: TaskService = Depends(get_task_service),
) -> TaskIngestResult:
    """Idempotent task ingest endpoint."""
    return await task_service.ingest_task(request)


@router.get("", response_model=list[dict])
async def list_tasks(
    status: Optional[str] = Query(None, description="Task status filter"),
    task_service: TaskService = Depends(get_task_service),
) -> list[dict]:
    """List tasks."""
    return await task_service.list_tasks(status=status)


@router.get("/review/queue", response_model=list[dict])
async def get_review_queue(
    limit: int = Query(50, ge=1, le=200),
    task_service: TaskService = Depends(get_task_service),
) -> list[dict]:
    """Get deterministic task review queue."""
    return await task_service.get_review_queue(limit=limit)


@router.get("/{task_id}", response_model=dict)
async def get_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service),
) -> dict:
    """Get task by id."""
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=dict)
async def patch_task(
    task_id: str,
    request: TaskPatchRequest,
    task_service: TaskService = Depends(get_task_service),
) -> dict:
    """Patch a task."""
    task = await task_service.patch_task(task_id, request)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("/{task_id}/complete", response_model=dict)
async def complete_task(
    task_id: str,
    rationale: Optional[str] = Query(None, description="Completion rationale"),
    task_service: TaskService = Depends(get_task_service),
) -> dict:
    """Mark a task as done."""
    task = await task_service.complete_task(task_id, rationale=rationale)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("/{task_id}/snooze", response_model=dict)
async def snooze_task(
    task_id: str,
    request: TaskSnoozeRequest,
    task_service: TaskService = Depends(get_task_service),
) -> dict:
    """Snooze a task until a timestamp."""
    task = await task_service.snooze_task(task_id, request)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("/{task_id}/link", response_model=dict)
async def link_task(
    task_id: str,
    request: TaskLinkRequest,
    task_service: TaskService = Depends(get_task_service),
) -> dict:
    """Link dependency tasks."""
    task = await task_service.link_task(task_id, request)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("/{task_id}/suggest-dependencies", response_model=list[dict])
async def suggest_dependencies(
    task_id: str,
    limit: int = Query(5, ge=1, le=20),
    task_service: TaskService = Depends(get_task_service),
) -> list[dict]:
    """Return dependency suggestions for a task (advisory only)."""
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return await task_service.suggest_dependencies(task_id, limit=limit)


@router.post("/{task_id}/suggest-split", response_model=list[dict])
async def suggest_split(
    task_id: str,
    task_service: TaskService = Depends(get_task_service),
) -> list[dict]:
    """Return task split suggestions (advisory only)."""
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return await task_service.suggest_split(task_id)


@router.post("/{task_id}/apply-suggestion", response_model=dict)
async def apply_suggestion(
    task_id: str,
    request: TaskApplySuggestionRequest,
    task_service: TaskService = Depends(get_task_service),
) -> dict:
    """Apply a suggestion explicitly (no auto-apply)."""
    result = await task_service.apply_suggestion(task_id, request)
    if not result.get("applied") and result.get("reason") == "task_not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if not result.get("applied"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("reason"))
    return result


@router.post("/{task_id}/reject-suggestion", response_model=dict)
async def reject_suggestion(
    task_id: str,
    request: TaskRejectSuggestionRequest,
    task_service: TaskService = Depends(get_task_service),
) -> dict:
    """Record explicit suggestion rejection feedback."""
    result = await task_service.reject_suggestion(task_id, request)
    if not result.get("rejected") and result.get("reason") == "task_not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return result
