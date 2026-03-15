"""Digest planning helpers for M13 orchestration flows."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from shared.contracts import CalendarProviderReadResult


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _serialize_task(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": str(item.get("task_id", "")),
        "title": item.get("title", "Untitled"),
        "priority": item.get("priority", "p2"),
        "status": item.get("status", "open"),
        "due_at": (
            item.get("due_at").isoformat()
            if hasattr(item.get("due_at"), "isoformat")
            else item.get("due_at")
        ),
        "urgency_score": item.get("urgency_score"),
        "urgency_explanation": item.get("urgency_explanation"),
    }


def merge_calendar_reads(read_results: list[CalendarProviderReadResult]) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    provider_status: dict[str, str] = {}
    warnings: list[str] = []
    errors: list[str] = []

    for result in read_results:
        provider_status[result.provider] = result.status
        warnings.extend([f"{result.provider}:{warning}" for warning in result.warnings])
        if result.error:
            errors.append(f"{result.provider}:{result.error}")
        for event in result.events:
            events.append(event.model_dump(mode="json"))

    events.sort(key=lambda item: item.get("starts_at") or "")
    return {
        "provider_status": provider_status,
        "warnings": warnings,
        "errors": errors,
        "degraded": any(result.status == "degraded" for result in read_results),
        "unconfigured": [
            result.provider for result in read_results if result.status == "unconfigured"
        ],
        "events": events,
    }


def build_monday_digest_payload(
    *,
    tasks: list[dict[str, Any]],
    today_attention: dict[str, Any],
    week_attention: dict[str, Any],
    calendar_reads: list[CalendarProviderReadResult],
    now: datetime,
) -> dict[str, Any]:
    calendar = merge_calendar_reads(calendar_reads)
    top_actionable = [
        _serialize_task(item) for item in (today_attention.get("top_actionable") or [])[:5]
    ]
    due_this_week = [
        _serialize_task(item) for item in (week_attention.get("due_this_week") or [])[:5]
    ]
    high_priority = [
        _serialize_task(item)
        for item in (week_attention.get("high_priority_without_due") or [])[:5]
    ]
    blocked = [_serialize_task(item) for item in (week_attention.get("blocked_summary") or [])[:5]]

    week_horizon = now + timedelta(days=7)
    open_tasks = [
        _serialize_task(task) for task in tasks if task.get("status") not in {"done", "cancelled"}
    ]
    weekly_lookahead = due_this_week + [item for item in high_priority if item not in due_this_week]

    day_ahead = [
        event
        for event in calendar["events"]
        if (parsed := _parse_timestamp(event.get("starts_at"))) is not None
        and now <= parsed <= now + timedelta(days=1)
    ][:8]
    upcoming_calendar = [
        event
        for event in calendar["events"]
        if (parsed := _parse_timestamp(event.get("starts_at"))) is not None
        and now <= parsed <= week_horizon
    ][:8]

    return {
        "digest_type": "monday_weekly_day_ahead",
        "generated_at": now.isoformat(),
        "top_actionable": top_actionable,
        "due_this_week": due_this_week,
        "high_priority_without_due": high_priority,
        "blocked_summary": blocked,
        "weekly_lookahead": weekly_lookahead,
        "day_ahead": day_ahead,
        "calendar": calendar,
        "open_task_count": len(open_tasks),
        "summary": {
            "weekly_items": len(weekly_lookahead),
            "day_ahead_items": len(day_ahead),
            "calendar_events_this_week": len(upcoming_calendar),
        },
    }


def build_weekday_day_ahead_payload(
    *,
    tasks: list[dict[str, Any]],
    today_attention: dict[str, Any],
    calendar_reads: list[CalendarProviderReadResult],
    now: datetime,
) -> dict[str, Any]:
    calendar = merge_calendar_reads(calendar_reads)
    top_actionable = [
        _serialize_task(item) for item in (today_attention.get("top_actionable") or [])[:5]
    ]
    due_next_72h = [
        _serialize_task(item) for item in (today_attention.get("due_next_72h") or [])[:5]
    ]
    stale_candidate = today_attention.get("stale_cleanup_candidate")

    day_ahead = [
        event
        for event in calendar["events"]
        if (parsed := _parse_timestamp(event.get("starts_at"))) is not None
        and now <= parsed <= now + timedelta(days=1)
    ][:8]
    open_tasks = [
        _serialize_task(task) for task in tasks if task.get("status") not in {"done", "cancelled"}
    ]

    return {
        "digest_type": "weekday_day_ahead",
        "generated_at": now.isoformat(),
        "top_actionable": top_actionable,
        "due_next_72h": due_next_72h,
        "stale_cleanup_candidate": _serialize_task(stale_candidate) if stale_candidate else None,
        "day_ahead": day_ahead,
        "calendar": calendar,
        "open_task_count": len(open_tasks),
        "summary": {
            "top_actionable": len(top_actionable),
            "day_ahead_items": len(day_ahead),
        },
    }
