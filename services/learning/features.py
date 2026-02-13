"""Deterministic feature extraction for attention/suggestion candidates."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .semantics import infer_reminder_feedback_semantics


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _priority_value(priority: str | None) -> float:
    return {"p0": 1.0, "p1": 0.75, "p2": 0.5, "p3": 0.25}.get(priority or "p2", 0.5)


def build_task_features(task: dict[str, Any], now: datetime | None = None) -> dict[str, float]:
    """Build deterministic task features from API-visible state."""
    ts = now or datetime.utcnow()

    due_at = _parse_datetime(task.get("due_at"))
    updated_at = _parse_datetime(task.get("updated_at"))
    do_not_start_before = _parse_datetime(task.get("do_not_start_before"))

    hours_to_due = 9999.0
    due_overdue = 0.0
    due_in_24h = 0.0
    due_in_72h = 0.0
    due_in_week = 0.0
    has_due = 0.0

    if due_at:
        has_due = 1.0
        delta_hours = (due_at - ts).total_seconds() / 3600.0
        hours_to_due = delta_hours
        due_overdue = 1.0 if delta_hours < 0 else 0.0
        due_in_24h = 1.0 if 0 <= delta_hours <= 24 else 0.0
        due_in_72h = 1.0 if 0 <= delta_hours <= 72 else 0.0
        due_in_week = 1.0 if 0 <= delta_hours <= 168 else 0.0

    age_hours = 0.0
    if updated_at:
        age_hours = max(0.0, (ts - updated_at).total_seconds() / 3600.0)

    blocked_by = task.get("blocked_by") or []
    labels = task.get("labels") or []

    return {
        "priority_value": _priority_value(task.get("priority")),
        "has_due": has_due,
        "hours_to_due": float(hours_to_due),
        "due_overdue": due_overdue,
        "due_in_24h": due_in_24h,
        "due_in_72h": due_in_72h,
        "due_in_week": due_in_week,
        "age_hours": float(age_hours),
        "is_blocked": 1.0 if task.get("status") == "blocked" else 0.0,
        "is_snoozed": 1.0 if task.get("status") == "snoozed" else 0.0,
        "has_future_start_gate": 1.0 if do_not_start_before and do_not_start_before > ts else 0.0,
        "blocked_count": float(len(blocked_by)),
        "needs_review": 1.0 if "needs_review" in labels else 0.0,
    }


def build_feedback_features(
    *,
    action: str,
    followup_action_within_minutes: int | None = None,
    snooze_minutes: int | None = None,
) -> dict[str, float]:
    """Build deterministic feedback features and weak-label targets.

    This keeps weak-label inference explicit and replayable from event-visible
    fields.
    """
    semantics = infer_reminder_feedback_semantics(
        action=action,
        followup_action_within_minutes=followup_action_within_minutes,
        snooze_minutes=snooze_minutes,
    )
    return {
        "action_dismissed": 1.0 if action == "dismissed" else 0.0,
        "action_snoozed": 1.0 if action == "snoozed" else 0.0,
        "followup_action_within_minutes": float(followup_action_within_minutes or -1),
        "snooze_minutes": float(snooze_minutes or -1),
        "target_usefulness": semantics.usefulness,
        "target_timing_fit": semantics.timing_fit,
        "target_interrupt_cost": semantics.interrupt_cost,
    }
