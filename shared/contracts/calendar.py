"""Shared contracts for normalized calendar provider reads."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

CalendarProvider = Literal["google", "zoho"]
CalendarReadStatus = Literal["ok", "degraded", "unconfigured"]


class CalendarEvent(BaseModel):
    provider: CalendarProvider
    provider_event_id: str
    source_calendar_id: str | None = None
    title: str = "(untitled)"
    starts_at: str
    ends_at: str
    all_day: bool = False
    status: str = "confirmed"
    location: str | None = None
    organizer: str | None = None
    attendee_count: int | None = None
    warnings: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class CalendarProviderReadResult(BaseModel):
    provider: CalendarProvider
    status: CalendarReadStatus
    events: list[CalendarEvent] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
