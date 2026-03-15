"""Tests for Zoho Calendar adapter behavior."""

import httpx
import pytest

from services.adapters.calendar import ZohoCalendarAdapter


@pytest.mark.asyncio
async def test_zoho_calendar_adapter_reads_and_normalizes_events():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Zoho-oauthtoken token-zoho"
        return httpx.Response(
            200,
            json={
                "events": [
                    {
                        "id": "z-1",
                        "title": "Customer Call",
                        "start": {"datetime": "2026-03-16T11:00:00Z"},
                        "end": {"datetime": "2026-03-16T11:45:00Z"},
                        "status": "confirmed",
                        "organizer_email": "owner@example.com",
                        "attendees": ["a@example.com"],
                    }
                ]
            },
        )

    adapter = ZohoCalendarAdapter(
        access_token="token-zoho",
        calendar_id="zoho-main",
        transport=httpx.MockTransport(handler),
    )

    result = await adapter.list_events()

    assert result.status == "ok"
    assert len(result.events) == 1
    assert result.events[0].provider == "zoho"
    assert result.events[0].source_calendar_id == "zoho-main"


@pytest.mark.asyncio
async def test_zoho_calendar_adapter_returns_degraded_on_provider_failure():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "service unavailable"})

    adapter = ZohoCalendarAdapter(
        access_token="token-zoho",
        calendar_id="zoho-main",
        transport=httpx.MockTransport(handler),
    )

    result = await adapter.list_events()

    assert result.status == "degraded"
    assert result.error is not None
    assert result.events == []
