"""Normalization helpers for calendar provider payloads."""

from __future__ import annotations

from typing import Any, Callable

from shared.contracts import CalendarEvent, CalendarProviderReadResult


def _extract_timestamp(value: Any) -> tuple[str | None, bool]:
    if isinstance(value, str):
        return value, False
    if isinstance(value, dict):
        if value.get("dateTime"):
            return str(value["dateTime"]), False
        if value.get("date"):
            return str(value["date"]), True
        if value.get("datetime"):
            return str(value["datetime"]), False
        if value.get("date_time"):
            return str(value["date_time"]), False
        if value.get("time"):
            return str(value["time"]), False
    return None, False


def _coerce_attendee_count(value: Any) -> int | None:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, int):
        return value
    return None


def _normalize_items(
    provider: str,
    items: list[dict[str, Any]],
    *,
    source_calendar_id: str | None,
    field_getter: Callable[[dict[str, Any]], dict[str, Any]],
) -> CalendarProviderReadResult:
    events: list[CalendarEvent] = []
    warnings: list[str] = []

    for index, raw_item in enumerate(items):
        fields = field_getter(raw_item)
        provider_event_id = fields.get("provider_event_id")
        starts_at, starts_all_day = _extract_timestamp(fields.get("starts_at"))
        ends_at, ends_all_day = _extract_timestamp(fields.get("ends_at"))

        item_warnings: list[str] = []
        if not provider_event_id:
            item_warnings.append("missing_event_id")
        if not starts_at:
            item_warnings.append("missing_start")
        if not ends_at:
            item_warnings.append("missing_end")

        if item_warnings:
            warnings.append(f"event[{index}]=" + ",".join(item_warnings))
            continue

        events.append(
            CalendarEvent(
                provider=provider,
                provider_event_id=str(provider_event_id),
                source_calendar_id=fields.get("source_calendar_id") or source_calendar_id,
                title=str(fields.get("title") or "(untitled)"),
                starts_at=str(starts_at),
                ends_at=str(ends_at),
                all_day=bool(starts_all_day or ends_all_day),
                status=str(fields.get("status") or "confirmed"),
                location=fields.get("location"),
                organizer=fields.get("organizer"),
                attendee_count=_coerce_attendee_count(fields.get("attendees")),
                warnings=item_warnings,
                raw=raw_item,
            )
        )

    return CalendarProviderReadResult(
        provider=provider,
        status="degraded" if warnings else "ok",
        events=events,
        warnings=warnings,
    )


def normalize_google_calendar_response(
    payload: dict[str, Any],
    *,
    source_calendar_id: str | None,
) -> CalendarProviderReadResult:
    items = payload.get("items") or []
    return _normalize_items(
        "google",
        items,
        source_calendar_id=source_calendar_id,
        field_getter=lambda raw_item: {
            "provider_event_id": raw_item.get("id"),
            "source_calendar_id": source_calendar_id,
            "title": raw_item.get("summary"),
            "starts_at": raw_item.get("start"),
            "ends_at": raw_item.get("end"),
            "status": raw_item.get("status"),
            "location": raw_item.get("location"),
            "organizer": (raw_item.get("organizer") or {}).get("email"),
            "attendees": raw_item.get("attendees"),
        },
    )


def normalize_zoho_calendar_response(
    payload: dict[str, Any],
    *,
    source_calendar_id: str | None,
) -> CalendarProviderReadResult:
    items = payload.get("events") or payload.get("items") or []
    return _normalize_items(
        "zoho",
        items,
        source_calendar_id=source_calendar_id,
        field_getter=lambda raw_item: {
            "provider_event_id": raw_item.get("id") or raw_item.get("uid"),
            "source_calendar_id": raw_item.get("calendar_id") or source_calendar_id,
            "title": raw_item.get("title") or raw_item.get("summary"),
            "starts_at": raw_item.get("start") or raw_item.get("start_time"),
            "ends_at": raw_item.get("end") or raw_item.get("end_time"),
            "status": raw_item.get("status"),
            "location": raw_item.get("location"),
            "organizer": raw_item.get("organizer") or raw_item.get("organizer_email"),
            "attendees": raw_item.get("attendees"),
        },
    )
