"""Deterministic attention service for Milestone 6."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from shared.contracts import (
    AttentionBucket,
    AttentionCandidate,
    AttentionScoringComputedEvent,
    FeatureSnapshotRecordedEvent,
    ModelScoreRecordedEvent,
)
from services.event_store.file_store import FileEventStore
from services.learning import ShadowRanker, build_task_features
from services.query.service import QueryService


class AttentionService:
    """Build reproducible attention queues from task state."""

    def __init__(
        self,
        event_store: FileEventStore,
        query_service: QueryService,
        enable_shadow_ranker: bool = True,
        shadow_confidence_threshold: float = 0.6,
        enable_bounded_personalization: bool = False,
    ):
        self.event_store = event_store
        self.query_service = query_service
        self.enable_shadow_ranker = enable_shadow_ranker
        self.shadow_confidence_threshold = shadow_confidence_threshold
        self.enable_bounded_personalization = enable_bounded_personalization
        self.ranker = ShadowRanker()
        self.bucket_rank = {
            AttentionBucket.URGENT_DUE_SOON: 0,
            AttentionBucket.READY_HIGH_PRIORITY: 1,
            AttentionBucket.READY_NORMAL: 2,
            AttentionBucket.BLOCKED: 3,
            AttentionBucket.DEFERRED_OR_GATED: 4,
            AttentionBucket.COMPLETED_OR_CANCELLED: 5,
        }

    async def get_today_attention(self, limit: int = 5) -> dict[str, Any]:
        now = datetime.utcnow()
        tasks = await self.query_service.get_tasks()

        scored = [await self._score_task(task, now) for task in tasks]
        actionable = [item for item in scored if item["is_actionable"]]
        actionable = self._sort_with_optional_personalization(actionable)

        due_72h = [
            item
            for item in scored
            if item["due_at"] is not None
            and 0 <= (item["due_at"] - now).total_seconds() <= 72 * 3600
            and item["status"] not in ("done", "cancelled")
        ]
        due_72h.sort(key=lambda item: item["due_at"])

        stale = [item for item in scored if item["is_stale"]]
        stale.sort(key=lambda item: item["updated_at"] or "")

        top_actionable = actionable[:limit]
        stale_candidate = stale[0] if stale else None

        await self._record_queue("today", top_actionable)

        return {
            "generated_at": now.isoformat(),
            "top_actionable": top_actionable,
            "due_next_72h": due_72h,
            "stale_cleanup_candidate": stale_candidate,
        }

    async def get_week_attention(self) -> dict[str, Any]:
        now = datetime.utcnow()
        tasks = await self.query_service.get_tasks()
        scored = [await self._score_task(task, now) for task in tasks]

        week_horizon = now + timedelta(days=7)
        due_this_week = [
            item
            for item in scored
            if item["due_at"] is not None
            and now <= item["due_at"] <= week_horizon
            and item["status"] not in ("done", "cancelled")
        ]
        due_this_week.sort(key=lambda item: item["due_at"])

        high_priority_no_due = [
            item
            for item in scored
            if item["due_at"] is None
            and item["priority"] in ("p0", "p1")
            and item["status"] not in ("done", "cancelled")
        ]
        high_priority_no_due = self._sort_with_optional_personalization(high_priority_no_due)

        blocked = [item for item in scored if item["status"] == "blocked"]
        blocked = self._sort_with_optional_personalization(blocked)

        await self._record_queue("week", due_this_week + high_priority_no_due + blocked)

        return {
            "generated_at": now.isoformat(),
            "due_this_week": due_this_week,
            "high_priority_without_due": high_priority_no_due,
            "blocked_summary": blocked,
        }

    async def run(self) -> dict[str, Any]:
        today = await self.get_today_attention()
        week = await self.get_week_attention()
        return {
            "status": "ok",
            "generated_at": datetime.utcnow().isoformat(),
            "today_counts": {
                "top_actionable": len(today["top_actionable"]),
                "due_next_72h": len(today["due_next_72h"]),
                "has_stale_candidate": today["stale_cleanup_candidate"] is not None,
            },
            "week_counts": {
                "due_this_week": len(week["due_this_week"]),
                "high_priority_without_due": len(week["high_priority_without_due"]),
                "blocked_summary": len(week["blocked_summary"]),
            },
        }

    def _deterministic_sort_key(self, item: dict[str, Any]) -> tuple[int, float, str]:
        return (
            item["deterministic_bucket_rank"],
            -item["urgency_score"],
            item["updated_at"] or "",
        )

    def _sort_with_optional_personalization(
        self, items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        deterministic = sorted(items, key=self._deterministic_sort_key)
        for candidate in deterministic:
            candidate["personalization_applied"] = False
            candidate["personalization_policy"] = (
                "bounded_in_bucket" if self.enable_bounded_personalization else "deterministic_only"
            )

        if not self.enable_bounded_personalization:
            return deterministic

        grouped: dict[int, list[dict[str, Any]]] = {}
        for item in deterministic:
            grouped.setdefault(item["deterministic_bucket_rank"], []).append(item)

        merged: list[dict[str, Any]] = []
        for rank in sorted(grouped):
            merged.extend(self._reorder_bucket_with_model(grouped[rank]))

        return merged

    def _reorder_bucket_with_model(
        self, bucket_items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        eligible = [
            item
            for item in bucket_items
            if item.get("model_score") is not None
            and (item.get("model_confidence") or 0.0) >= self.shadow_confidence_threshold
        ]

        if len(eligible) < 2:
            return bucket_items

        ordered_eligible = sorted(
            eligible,
            key=lambda item: (
                -float(item.get("model_score") or 0.0),
                -item["urgency_score"],
                item["updated_at"] or "",
            ),
        )

        eligible_ids_before = [item["task_id"] for item in eligible]
        eligible_ids_after = [item["task_id"] for item in ordered_eligible]
        if eligible_ids_before == eligible_ids_after:
            return bucket_items

        iterator = iter(ordered_eligible)
        updated: list[dict[str, Any]] = []
        eligible_set = set(eligible_ids_before)
        for item in bucket_items:
            if item["task_id"] in eligible_set:
                chosen = next(iterator)
                chosen["personalization_applied"] = True
                updated.append(chosen)
            else:
                updated.append(item)

        return updated

    async def _record_queue(self, queue_name: str, items: list[dict[str, Any]]) -> None:
        event = AttentionScoringComputedEvent(
            queue_name=queue_name,
            candidates=[
                AttentionCandidate(
                    task_id=item["task_id"],
                    urgency_score=item["urgency_score"],
                    explanation=item["urgency_explanation"],
                    deterministic_bucket_id=item["deterministic_bucket_id"],
                    deterministic_bucket_rank=item["deterministic_bucket_rank"],
                    deterministic_explanation=item["deterministic_explanation"],
                    model_score=item.get("model_score"),
                    model_confidence=item.get("model_confidence"),
                    learned_explanation=item.get("learned_explanation"),
                    personalization_applied=item.get("personalization_applied", False),
                    personalization_policy=item.get("personalization_policy", "deterministic_only"),
                    shadow_score=item.get("shadow_score"),
                    shadow_confidence=item.get("shadow_confidence"),
                )
                for item in items
            ],
            metadata={"service": "attention_service"},
        )
        await self.event_store.append(event)

    async def _score_task(self, task: dict[str, Any], now: datetime) -> dict[str, Any]:
        due_at = self.query_service._parse_iso(task.get("due_at"))
        updated_at = self.query_service._parse_iso(task.get("updated_at"))
        do_not_start_before = self.query_service._parse_iso(task.get("do_not_start_before"))
        is_stale = self.query_service._is_task_stale(task)

        components: list[str] = []
        score = 0.0

        if due_at:
            hours_to_due = (due_at - now).total_seconds() / 3600.0
            if hours_to_due < 0:
                score += 60
                components.append("overdue +60")
            elif hours_to_due <= 24:
                score += 45
                components.append("due<24h +45")
            elif hours_to_due <= 72:
                score += 35
                components.append("due<72h +35")
            elif hours_to_due <= 7 * 24:
                score += 20
                components.append("due<7d +20")
            else:
                score += 5
                components.append("due>7d +5")

        priority = task.get("priority", "p2")
        priority_delta = {"p0": 30, "p1": 20, "p2": 10, "p3": 0}.get(priority, 0)
        score += priority_delta
        components.append(f"priority {priority} +{priority_delta}")

        if updated_at:
            age_days = max(0.0, (now - updated_at).total_seconds() / (24 * 3600))
            if age_days >= 14:
                score += 18
                components.append("age>=14d +18")
            elif age_days >= 7:
                score += 12
                components.append("age>=7d +12")
            elif age_days >= 3:
                score += 6
                components.append("age>=3d +6")

        status = task.get("status", "open")
        if status == "blocked":
            score -= 15
            components.append("blocked -15")
        if status == "snoozed":
            score -= 25
            components.append("snoozed -25")

        if do_not_start_before and do_not_start_before > now:
            score -= 30
            components.append("start-gated -30")

        deterministic_bucket_id = self._determine_bucket(
            status=status,
            priority=priority,
            due_at=due_at,
            do_not_start_before=do_not_start_before,
            now=now,
        )
        deterministic_bucket_rank = self.bucket_rank[deterministic_bucket_id]

        is_actionable = status in ("open", "in_progress") and not (
            do_not_start_before and do_not_start_before > now
        )

        candidate = {
            "task_id": task.get("task_id"),
            "title": task.get("title"),
            "status": status,
            "priority": priority,
            "due_at": due_at,
            "updated_at": task.get("updated_at"),
            "is_stale": is_stale,
            "is_actionable": is_actionable,
            "urgency_score": round(score, 2),
            "urgency_explanation": "; ".join(components) if components else "baseline",
            "deterministic_bucket_id": deterministic_bucket_id,
            "deterministic_bucket_rank": deterministic_bucket_rank,
            "deterministic_explanation": "; ".join(components) if components else "baseline",
            "model_score": None,
            "model_confidence": None,
            "learned_explanation": None,
            "personalization_applied": False,
            "personalization_policy": "deterministic_only",
        }

        features = build_task_features(task, now)
        snapshot_event = FeatureSnapshotRecordedEvent(
            candidate_id=str(task.get("task_id")),
            candidate_type="attention_task",
            features=features,
            context={
                "status": status,
                "priority": priority,
                "deterministic_bucket_id": deterministic_bucket_id,
                "deterministic_bucket_rank": deterministic_bucket_rank,
            },
            metadata={"service": "attention_service"},
        )

        await self.event_store.append(snapshot_event)

        if self.enable_shadow_ranker:
            try:
                result = self.ranker.score(features)
                candidate["shadow_score"] = result.score
                candidate["shadow_confidence"] = result.confidence
                candidate["shadow_explanation"] = result.explanation
                candidate["model_score"] = result.score
                candidate["model_confidence"] = result.confidence
                candidate["learned_explanation"] = result.explanation
                model_event = ModelScoreRecordedEvent(
                    candidate_id=str(task.get("task_id")),
                    candidate_type="attention_task",
                    model_name=self.ranker.model_name,
                    model_version=self.ranker.model_version,
                    score=result.score,
                    confidence=result.confidence,
                    explanation=result.explanation,
                    metadata={
                        "service": "attention_service",
                        "mode": "shadow",
                        "deterministic_bucket_id": deterministic_bucket_id,
                    },
                )
                await self.event_store.append(model_event)
            except Exception:
                candidate["shadow_score"] = None
                candidate["shadow_confidence"] = None
                candidate["shadow_explanation"] = (
                    "shadow model unavailable; deterministic fallback active"
                )
                candidate["model_score"] = None
                candidate["model_confidence"] = None
                candidate["learned_explanation"] = (
                    "shadow model unavailable; deterministic fallback active"
                )

        return candidate

    def _determine_bucket(
        self,
        *,
        status: str,
        priority: str,
        due_at: datetime | None,
        do_not_start_before: datetime | None,
        now: datetime,
    ) -> AttentionBucket:
        if status in ("done", "cancelled"):
            return AttentionBucket.COMPLETED_OR_CANCELLED

        if status == "blocked":
            return AttentionBucket.BLOCKED

        if status == "snoozed" or (do_not_start_before and do_not_start_before > now):
            return AttentionBucket.DEFERRED_OR_GATED

        if due_at is not None:
            hours_to_due = (due_at - now).total_seconds() / 3600.0
            if hours_to_due <= 72:
                return AttentionBucket.URGENT_DUE_SOON

        if priority in ("p0", "p1"):
            return AttentionBucket.READY_HIGH_PRIORITY

        return AttentionBucket.READY_NORMAL
