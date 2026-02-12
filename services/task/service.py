"""Task service for Milestone 5 task lifecycle operations."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Optional
from uuid import UUID

from shared.contracts import (
    DecisionRecordedEvent,
    FeatureSnapshotRecordedEvent,
    SuggestionAppliedEvent,
    SuggestionEditedEvent,
    SuggestionRejectedEvent,
    SuggestionShownEvent,
    SuggestionType,
    SourceType,
    Task,
    TaskApplySuggestionRequest,
    TaskExplanation,
    TaskIngestRequest,
    TaskIngestResult,
    TaskLinkRequest,
    TaskPatchRequest,
    TaskPriority,
    TaskRejectSuggestionRequest,
    TaskSnoozeRequest,
    TaskSuggestion,
    TaskStatus,
    TASK_LABEL_NEEDS_REVIEW,
)
from services.learning import build_task_features
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

    async def suggest_dependencies(self, task_id: str, limit: int = 5) -> list[dict]:
        task = await self.query_service.get_task_by_id(task_id)
        if not task:
            return []

        candidates = []
        all_tasks = await self.query_service.get_tasks()
        task_labels = set(task.get("labels") or [])
        task_project = task.get("project")

        for other in all_tasks:
            other_id = other.get("task_id")
            if other_id == task_id:
                continue
            if other.get("status") in (TaskStatus.DONE.value, TaskStatus.CANCELLED.value):
                continue
            if self._would_create_cycle(task_id, other_id):
                continue

            score = 0
            rationale_bits: list[str] = []

            if task_project and task_project == other.get("project"):
                score += 3
                rationale_bits.append("same project")

            other_labels = set(other.get("labels") or [])
            overlap = task_labels.intersection(other_labels)
            if overlap:
                score += 2
                rationale_bits.append(f"shared labels: {', '.join(sorted(overlap))}")

            if other.get("priority") in (TaskPriority.P0.value, TaskPriority.P1.value):
                score += 1
                rationale_bits.append("high-priority dependency")

            if score <= 0:
                continue

            payload = {"blocked_by": [other_id]}
            suggestion_id = self._make_suggestion_id(
                task_id, SuggestionType.DEPENDENCY.value, payload
            )
            suggestion = TaskSuggestion(
                suggestion_id=suggestion_id,
                task_id=UUID(task_id),
                suggestion_type=SuggestionType.DEPENDENCY,
                rationale="; ".join(rationale_bits) or "Potential prerequisite task",
                payload=payload,
            )
            candidates.append((score, suggestion))

        ordered = [
            entry[1] for entry in sorted(candidates, key=lambda item: item[0], reverse=True)[:limit]
        ]
        for candidate in ordered:
            await self._record_suggestion_shown(task_id, candidate)
        return [item.model_dump(mode="json") for item in ordered]

    async def suggest_split(self, task_id: str) -> list[dict]:
        task = await self.query_service.get_task_by_id(task_id)
        if not task:
            return []

        title = task.get("title", "Task")
        body = task.get("body") or ""
        project = task.get("project")

        split_steps = [
            {
                "title": f"Clarify scope: {title}",
                "body": "Define success criteria and constraints.",
            },
            {
                "title": f"Execute core work: {title}",
                "body": body or "Implement the main execution step.",
            },
            {
                "title": f"Verify and close: {title}",
                "body": "Validate outcome, document, and mark done.",
            },
        ]
        payload = {"subtasks": split_steps, "project": project}
        suggestion = TaskSuggestion(
            suggestion_id=self._make_suggestion_id(task_id, SuggestionType.SPLIT.value, payload),
            task_id=UUID(task_id),
            suggestion_type=SuggestionType.SPLIT,
            rationale="Task appears broad; split into clarify/execute/verify steps",
            payload=payload,
        )

        await self._record_suggestion_shown(task_id, suggestion)
        return [suggestion.model_dump(mode="json")]

    async def apply_suggestion(self, task_id: str, request: TaskApplySuggestionRequest) -> dict:
        existing = await self.query_service.get_task_by_id(task_id)
        if not existing:
            return {"applied": False, "reason": "task_not_found"}

        payload = request.edited_payload or request.payload
        if request.edited_payload and request.edited_payload != request.payload:
            await self.event_store.append(
                SuggestionEditedEvent(
                    task_id=task_id,
                    suggestion_id=request.suggestion_id,
                    suggestion_type=request.suggestion_type.value,
                    original_payload=request.payload,
                    edited_payload=request.edited_payload,
                    rationale=request.rationale,
                    metadata={"service": "task_service"},
                )
            )

        created_task_ids: list[str] = []
        updated_task: Optional[dict] = None

        if request.suggestion_type == SuggestionType.DEPENDENCY:
            blocked_by = payload.get("blocked_by") or []
            link_request = TaskLinkRequest(blocked_by=[UUID(dep_id) for dep_id in blocked_by])
            updated_task = await self.link_task(task_id, link_request)
        elif request.suggestion_type == SuggestionType.SPLIT:
            subtasks = payload.get("subtasks") or []
            for index, subtask in enumerate(subtasks):
                source_ref = f"suggestion:{request.suggestion_id}:split:{index}"
                ingest_result = await self.ingest_task(
                    TaskIngestRequest(
                        title=subtask.get("title") or f"Subtask {index + 1}",
                        body=subtask.get("body"),
                        source=SourceType.API,
                        source_ref=source_ref,
                        priority=TaskPriority(existing.get("priority", TaskPriority.P2.value)),
                        labels=list(
                            dict.fromkeys((existing.get("labels") or []) + ["generated_split"])
                        ),
                        project=payload.get("project") or existing.get("project"),
                    )
                )
                created_task_ids.append(str(ingest_result.task_id))
            updated_task = await self.patch_task(
                task_id,
                TaskPatchRequest(
                    labels=list(dict.fromkeys((existing.get("labels") or []) + ["split_parent"]))
                ),
            )
        else:
            return {"applied": False, "reason": "unsupported_suggestion_type"}

        await self.event_store.append(
            SuggestionAppliedEvent(
                task_id=task_id,
                suggestion_id=request.suggestion_id,
                suggestion_type=request.suggestion_type.value,
                applied_payload=payload,
                rationale=request.rationale,
                metadata={"service": "task_service"},
            )
        )

        return {
            "applied": True,
            "task": updated_task,
            "created_task_ids": created_task_ids,
        }

    async def reject_suggestion(self, task_id: str, request: TaskRejectSuggestionRequest) -> dict:
        existing = await self.query_service.get_task_by_id(task_id)
        if not existing:
            return {"rejected": False, "reason": "task_not_found"}

        await self.event_store.append(
            SuggestionRejectedEvent(
                task_id=task_id,
                suggestion_id=request.suggestion_id,
                suggestion_type=request.suggestion_type.value,
                rationale=request.rationale,
                metadata={"service": "task_service"},
            )
        )
        return {"rejected": True}

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

    def _make_suggestion_id(self, task_id: str, suggestion_type: str, payload: dict) -> str:
        key = f"{task_id}|{suggestion_type}|{payload}"
        return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]

    def _would_create_cycle(self, task_id: str, dependency_id: str) -> bool:
        graph: dict[str, set[str]] = {}
        rows = self.query_service.conn.execute("SELECT task_id, blocked_by FROM tasks").fetchall()
        for row in rows:
            blocked_raw = row["blocked_by"]
            blocked_ids: set[str] = set()
            if blocked_raw:
                try:
                    import json

                    blocked_ids = set(json.loads(blocked_raw))
                except Exception:
                    blocked_ids = set()
            graph[row["task_id"]] = blocked_ids

        graph.setdefault(task_id, set()).add(dependency_id)

        visited: set[str] = set()
        stack: set[str] = set()

        def visit(node: str) -> bool:
            if node in stack:
                return True
            if node in visited:
                return False
            visited.add(node)
            stack.add(node)
            for neighbor in graph.get(node, set()):
                if visit(neighbor):
                    return True
            stack.remove(node)
            return False

        return visit(task_id)

    async def _record_suggestion_shown(self, task_id: str, suggestion: TaskSuggestion) -> None:
        await self.event_store.append(
            SuggestionShownEvent(
                task_id=task_id,
                suggestion_id=suggestion.suggestion_id,
                suggestion_type=suggestion.suggestion_type.value,
                suggestion_payload=suggestion.payload,
                rationale=suggestion.rationale,
                metadata={"service": "task_service"},
            )
        )
        task = await self.query_service.get_task_by_id(task_id)
        if task:
            await self.event_store.append(
                FeatureSnapshotRecordedEvent(
                    candidate_id=suggestion.suggestion_id,
                    candidate_type=f"suggestion_{suggestion.suggestion_type.value}",
                    features=build_task_features(task),
                    context={"task_id": task_id},
                    metadata={"service": "task_service"},
                )
            )
