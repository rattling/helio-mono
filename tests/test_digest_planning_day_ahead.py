"""Tests for weekday day-ahead digest planning."""

from datetime import datetime

from shared.contracts import CalendarEvent, CalendarProviderReadResult
from services.orchestration.planning import build_weekday_day_ahead_payload


def test_build_weekday_day_ahead_payload_merges_attention_and_calendar():
    payload = build_weekday_day_ahead_payload(
        tasks=[
            {
                "task_id": "task-1",
                "title": "Review queue",
                "priority": "p0",
                "status": "open",
                "due_at": None,
            }
        ],
        today_attention={
            "top_actionable": [
                {
                    "task_id": "task-1",
                    "title": "Review queue",
                    "priority": "p0",
                    "status": "open",
                    "urgency_score": 91,
                }
            ],
            "due_next_72h": [
                {
                    "task_id": "task-2",
                    "title": "Ship milestone",
                    "priority": "p1",
                    "status": "open",
                    "due_at": "2026-03-19T09:00:00",
                }
            ],
            "stale_cleanup_candidate": None,
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
                        title="Customer Call",
                        starts_at="2026-03-18T10:00:00Z",
                        ends_at="2026-03-18T10:30:00Z",
                    )
                ],
            ),
            CalendarProviderReadResult(provider="zoho", status="unconfigured"),
        ],
        now=datetime(2026, 3, 18, 9, 0, 0),
    )

    assert payload["digest_type"] == "weekday_day_ahead"
    assert payload["top_actionable"][0]["title"] == "Review queue"
    assert payload["day_ahead"][0]["title"] == "Customer Call"
    assert payload["calendar"]["provider_status"]["zoho"] == "unconfigured"
