"""Tests for normalized calendar contract behavior."""

from services.adapters.calendar import (
    normalize_google_calendar_response,
    normalize_zoho_calendar_response,
)
from shared.contracts import CalendarEvent


def test_google_normalization_marks_partial_payload_as_degraded():
    result = normalize_google_calendar_response(
        {
            "items": [
                {
                    "id": "g-valid",
                    "summary": "Working Session",
                    "start": {"dateTime": "2026-03-17T08:00:00Z"},
                    "end": {"dateTime": "2026-03-17T09:00:00Z"},
                },
                {
                    "id": "g-missing-end",
                    "summary": "Broken Event",
                    "start": {"dateTime": "2026-03-17T10:00:00Z"},
                },
            ]
        },
        source_calendar_id="primary",
    )

    assert result.status == "degraded"
    assert len(result.events) == 1
    assert result.warnings == ["event[1]=missing_end"]


def test_zoho_normalization_supports_all_day_events():
    result = normalize_zoho_calendar_response(
        {
            "events": [
                {
                    "id": "z-all-day",
                    "title": "Offsite",
                    "start": {"date": "2026-03-18"},
                    "end": {"date": "2026-03-19"},
                }
            ]
        },
        source_calendar_id="zoho-main",
    )

    assert result.status == "ok"
    assert result.events[0].all_day is True
    assert (
        CalendarEvent.model_validate(result.events[0].model_dump()).provider_event_id == "z-all-day"
    )
