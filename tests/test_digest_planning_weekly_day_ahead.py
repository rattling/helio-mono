"""Tests for Monday weekly plus day-ahead digest planning."""

from datetime import datetime

from shared.contracts import CalendarEvent, CalendarProviderReadResult
from services.orchestration.planning import build_monday_digest_payload


def test_build_monday_digest_payload_merges_attention_tasks_and_calendar():
    payload = build_monday_digest_payload(
        tasks=[
            {
                "task_id": "task-1",
                "title": "Ship milestone",
                "priority": "p1",
                "status": "open",
                "due_at": "2026-03-18T09:00:00",
            },
            {
                "task_id": "task-2",
                "title": "Review queue",
                "priority": "p0",
                "status": "open",
                "due_at": None,
            },
        ],
        today_attention={
            "top_actionable": [
                {
                    "task_id": "task-2",
                    "title": "Review queue",
                    "priority": "p0",
                    "status": "open",
                    "urgency_score": 91,
                }
            ]
        },
        week_attention={
            "due_this_week": [
                {
                    "task_id": "task-1",
                    "title": "Ship milestone",
                    "priority": "p1",
                    "status": "open",
                    "due_at": "2026-03-18T09:00:00",
                }
            ],
            "high_priority_without_due": [
                {
                    "task_id": "task-2",
                    "title": "Review queue",
                    "priority": "p0",
                    "status": "open",
                    "due_at": None,
                }
            ],
            "blocked_summary": [],
        },
        calendar_reads=[
            CalendarProviderReadResult(
                provider="google",
                status="ok",
                events=[
                    CalendarEvent(
                        provider="google",
                        provider_event_id="g-1",
                        source_calendar_id="primary",
                        title="Team Sync",
                        starts_at="2026-03-16T10:00:00Z",
                        ends_at="2026-03-16T10:30:00Z",
                    )
                ],
            ),
            CalendarProviderReadResult(
                provider="zoho",
                status="degraded",
                warnings=["event[0]=missing_end"],
            ),
        ],
        now=datetime(2026, 3, 16, 9, 0, 0),
    )

    assert payload["digest_type"] == "monday_weekly_day_ahead"
    assert payload["weekly_lookahead"][0]["title"] == "Ship milestone"
    assert payload["day_ahead"][0]["title"] == "Team Sync"
    assert payload["calendar"]["degraded"] is True
    assert payload["calendar"]["provider_status"]["google"] == "ok"
    assert payload["calendar"]["provider_status"]["zoho"] == "degraded"
