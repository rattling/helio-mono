"""Task service for Milestone 5 task lifecycle operations."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Optional
from uuid import UUID

from shared.contracts import (
    DecisionRecordedEvent,
    SourceType,
    Task,
    TaskExplanation,
    TaskIngestRequest,
    TaskIngestResult,
    TaskLinkRequest,
    TaskPatchRequest,
    TaskPriority,
    TaskSnoozeRequest,
    TaskStatus,
    TASK_LABEL_NEEDS_REVIEW,
)
from services.event_store.file_store import FileEventStore
from services.query.service import QueryService


class TaskService:
    """Domain service for task ingest and lifecycle mutations."""

    def __init__(self, event_store: FileEventStore, query_service: QueryService):
        self.event_store = event_store
        self.query_service = query_service

    async def ingest_task(self, request: TaskIngestRequest) -> TaskIngestResult:
        """Idempotent ingest via (source, source_ref) with deterministic dedup."""
        existing = self.query_service.conn.execute(
            "SELECT task_id FROM tasks WHERE source = ? AND source_ref = ?",
            (request.source.value, request.source_ref),
        ).fetchone()

        if existing:
            task_id = existing["task_id"]
            decision_rationale = "Idempotent ingest hit existing task for source/source_ref"
            existing_task = await self.query_service.get_task_by_id(task_id)
            await self._record_decision(
                action="ingest_existing",
                rationale=decision_rationale,
                task_snapshot=existing_task,
                source=request.source,
                source_ref=request.source_ref,
            )
            return TaskIngestResult(
                task_id=UUID(task_id), created=False, decision_rationale=decision_rationale
            )

        dedup_group_id = self._compute_dedup_group_id(request.title, request.body, request.project)

        duplicate_count_row = self.query_service.conn.execute(
            "SELECT COUNT(*) AS cnt FROM tasks WHERE dedup_group_id = ? AND status NOT IN (?, ?)",
            (dedup_group_id, TaskStatus.DONE.value, TaskStatus.CANCELLED.value),
        ).fetchone()
        duplicate_count = int(duplicate_count_row["cnt"]) if duplicate_count_row else 0

        labels = list(dict.fromkeys(request.labels))
        decision_rationale = "New task created"
        if duplicate_count > 0 and TASK_LABEL_NEEDS_REVIEW not in labels:
            labels.append(TASK_LABEL_NEEDS_REVIEW)
            decision_rationale = (
                f"Potential duplicate detected (dedup group {dedup_group_id}); "
                "created and flagged for review"
            )

        now = datetime.utcnow()
        task = Task(
            title=request.title,
            body=request.body,
            source=request.source,
            source_ref=request.source_ref,
            priority=request.priority or TaskPriority.P2,
            due_at=request.due_at,
            do_not_start_before=request.do_not_start_before,
            labels=labels,
            project=request.project,
            dedup_group_id=dedup_group_id,
            created_at=now,
            updated_at=now,
            explanations=[
                TaskExplanation(
                    actor="task_service",
                    action="ingest",
                    rationale=decision_rationale,
                )
            ],
        )

        await self.query_service._upsert_task(task.model_dump(mode="json"))
        self.query_service.conn.commit()

        await self._record_decision(
            action="ingest_created",
            rationale=decision_rationale,
            task_snapshot=task.model_dump(mode="json"),
            source=request.source,
            source_ref=request.source_ref,
        )

        return TaskIngestResult(
            task_id=task.task_id, created=True, decision_rationale=decision_rationale
        )

    async def list_tasks(self, status: Optional[str] = None) -> list[dict]:
        return await self.query_service.get_tasks(status=status)

    async def get_task(self, task_id: str) -> Optional[dict]:
        return await self.query_service.get_task_by_id(task_id)

    async def patch_task(self, task_id: str, patch: TaskPatchRequest) -> Optional[dict]:
        existing = await self.query_service.get_task_by_id(task_id)
        if not existing:
            return None

        task = Task(**existing)
        updates = patch.model_dump(exclude_none=True)
        for key, value in updates.items():
            setattr(task, key, value)

        task.updated_at = datetime.utcnow()
        task.explanations.append(
            TaskExplanation(
                actor="task_service",
                action="patch",
                rationale="Task updated via PATCH",
            )
        )

        await self.query_service._upsert_task(task.model_dump(mode="json"))
        self.query_service.conn.commit()
        updated = await self.query_service.get_task_by_id(task_id)
        await self._record_decision(
            action="patch",
            rationale="Task updated via PATCH",
            task_snapshot=updated,
            source=SourceType.API,
            source_ref=f"task:{task_id}:patch:{task.updated_at.isoformat()}",
        )
        return updated

    async def complete_task(self, task_id: str, rationale: Optional[str] = None) -> Optional[dict]:
        existing = await self.query_service.get_task_by_id(task_id)
        if not existing:
            return None

        task = Task(**existing)
        now = datetime.utcnow()
        task.status = TaskStatus.DONE
        task.completed_at = now
        task.updated_at = now
        task.explanations.append(
            TaskExplanation(
                actor="task_service",
                action="complete",
                rationale=rationale or "Task marked done",
            )
        )

        await self.query_service._upsert_task(task.model_dump(mode="json"))
        self.query_service.conn.commit()
        updated = await self.query_service.get_task_by_id(task_id)

        await self._record_decision(
            action="complete",
            rationale=rationale or "Task marked done",
            task_snapshot=updated,
            source=SourceType.API,
            source_ref=f"task:{task_id}:complete:{now.isoformat()}",
        )
        return updated

    async def snooze_task(self, task_id: str, request: TaskSnoozeRequest) -> Optional[dict]:
        existing = await self.query_service.get_task_by_id(task_id)
        if not existing:
            return None

        task = Task(**existing)
        task.status = TaskStatus.SNOOZED
        task.do_not_start_before = request.until
        task.updated_at = datetime.utcnow()
        task.explanations.append(
            TaskExplanation(
                actor="task_service",
                action="snooze",
                rationale=request.rationale or "Task snoozed",
            )
        )

        await self.query_service._upsert_task(task.model_dump(mode="json"))
        self.query_service.conn.commit()
        updated = await self.query_service.get_task_by_id(task_id)
        await self._record_decision(
            action="snooze",
            rationale=request.rationale or "Task snoozed",
            task_snapshot=updated,
            source=SourceType.API,
            source_ref=f"task:{task_id}:snooze:{task.updated_at.isoformat()}",
        )
        return updated

    async def link_task(self, task_id: str, request: TaskLinkRequest) -> Optional[dict]:
        existing = await self.query_service.get_task_by_id(task_id)
        if not existing:
            return None

        task = Task(**existing)
        existing_links = {str(item) for item in task.blocked_by}
        for dependency in request.blocked_by:
            existing_links.add(str(dependency))

        task.blocked_by = [UUID(item) for item in sorted(existing_links)]
        task.status = TaskStatus.BLOCKED if task.blocked_by else task.status
        task.updated_at = datetime.utcnow()
        task.explanations.append(
            TaskExplanation(
                actor="task_service",
                action="link",
                rationale=request.rationale or "Task dependencies updated",
            )
        )

        await self.query_service._upsert_task(task.model_dump(mode="json"))
        self.query_service.conn.commit()
        updated = await self.query_service.get_task_by_id(task_id)
        await self._record_decision(
            action="link",
            rationale=request.rationale or "Task dependencies updated",
            task_snapshot=updated,
            source=SourceType.API,
            source_ref=f"task:{task_id}:link:{task.updated_at.isoformat()}",
        )
        return updated

    async def get_review_queue(self, limit: int = 50) -> list[dict]:
        return await self.query_service.get_review_queue(limit=limit)

    async def _record_decision(
        self,
        action: str,
        rationale: str,
        task_snapshot: Optional[dict],
        source: SourceType,
        source_ref: str,
    ) -> None:
        event = DecisionRecordedEvent(
            decision_data={
                "domain": "task",
                "action": action,
                "source": source.value,
                "source_ref": source_ref,
                "task_snapshot": task_snapshot,
            },
            rationale=rationale,
            metadata={"service": "task_service"},
        )
        await self.event_store.append(event)

    def _compute_dedup_group_id(
        self, title: str, body: Optional[str], project: Optional[str]
    ) -> str:
        normalized_title = " ".join((title or "").lower().split())
        normalized_body = " ".join((body or "").lower().split())
        normalized_project = " ".join((project or "").lower().split())
        key = f"{normalized_title}|{normalized_body}|{normalized_project}"
        return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
