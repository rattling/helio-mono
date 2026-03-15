"""Tests for Google Calendar adapter behavior."""

import httpx
import pytest

from services.adapters.calendar import GoogleCalendarAdapter


@pytest.mark.asyncio
async def test_google_calendar_adapter_reads_and_normalizes_events():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer token-google"
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": "g-1",
                        "summary": "Team Sync",
                        "start": {"dateTime": "2026-03-16T09:00:00Z"},
                        "end": {"dateTime": "2026-03-16T09:30:00Z"},
                        "status": "confirmed",
                        "location": "Room 1",
                        "organizer": {"email": "ops@example.com"},
                        "attendees": [{"email": "a@example.com"}, {"email": "b@example.com"}],
                    }
                ]
            },
        )

    adapter = GoogleCalendarAdapter(
        access_token="token-google",
        calendar_id="primary",
        transport=httpx.MockTransport(handler),
    )

    result = await adapter.list_events()

    assert result.status == "ok"
    assert len(result.events) == 1
    assert result.events[0].provider == "google"
    assert result.events[0].title == "Team Sync"
    assert result.events[0].attendee_count == 2


@pytest.mark.asyncio
async def test_google_calendar_adapter_returns_unconfigured_when_credentials_missing():
    adapter = GoogleCalendarAdapter(access_token=None, calendar_id=None)

    result = await adapter.list_events()

    assert result.status == "unconfigured"
    assert result.error == "missing_credentials"
