"""Zoho Calendar read adapter for M13."""

from __future__ import annotations

import httpx

from shared.contracts import CalendarProviderReadResult
from services.adapters.calendar.normalize import normalize_zoho_calendar_response


class ZohoCalendarAdapter:
    def __init__(
        self,
        *,
        access_token: str | None,
        calendar_id: str | None,
        base_url: str = "https://calendar.zoho.com/api/v1",
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.access_token = access_token
        self.calendar_id = calendar_id
        self.base_url = base_url.rstrip("/")
        self.transport = transport

    async def list_events(
        self,
        *,
        time_min: str | None = None,
        time_max: str | None = None,
        calendar_id: str | None = None,
    ) -> CalendarProviderReadResult:
        resolved_calendar_id = calendar_id or self.calendar_id
        if not self.access_token or not resolved_calendar_id:
            return CalendarProviderReadResult(
                provider="zoho",
                status="unconfigured",
                error="missing_credentials",
            )

        params = {}
        if time_min:
            params["from"] = time_min
        if time_max:
            params["to"] = time_max

        headers = {"Authorization": f"Zoho-oauthtoken {self.access_token}"}
        url = f"{self.base_url}/calendars/{resolved_calendar_id}/events"

        try:
            async with httpx.AsyncClient(transport=self.transport) as client:
                response = await client.get(url, params=params, headers=headers, timeout=10.0)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            return CalendarProviderReadResult(
                provider="zoho",
                status="degraded",
                error=f"provider_request_failed:{exc.__class__.__name__}",
                warnings=[str(exc)],
            )

        return normalize_zoho_calendar_response(
            response.json(),
            source_calendar_id=resolved_calendar_id,
        )
