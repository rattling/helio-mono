"""Email renderers for digest payloads."""

from __future__ import annotations

from datetime import datetime


def _display_timestamp(value: str | None) -> str:
    if not value:
        return "unscheduled"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value


def _render_section(title: str, lines: list[str]) -> list[str]:
    rendered = [title]
    rendered.extend(lines or ["- None"])
    rendered.append("")
    return rendered


def format_attention_daily_digest_email(payload: dict) -> dict[str, str]:
    """Render a plain-text weekday day-ahead digest for email delivery."""
    digest_type = payload.get("digest_type") or "daily_digest"
    subject = "Helionyx Day-Ahead Digest"
    if digest_type == "weekday_day_ahead":
        subject = "Helionyx Weekday Day-Ahead Digest"

    top_actionable = payload.get("top_actionable") or []
    day_ahead = payload.get("day_ahead") or []
    due_next_72h = payload.get("due_next_72h") or []
    provider_status = ((payload.get("calendar") or {}).get("provider_status") or {}).items()

    lines = [subject, "=" * len(subject), ""]
    lines.extend(
        _render_section(
            "Top actionable",
            [
                f"- {item.get('title', 'Untitled')} [{item.get('priority', 'p2')}]"
                for item in top_actionable[:5]
            ],
        )
    )
    lines.extend(
        _render_section(
            "Day-ahead schedule",
            [
                f"- {event.get('title', 'Untitled')} ({_display_timestamp(event.get('starts_at'))})"
                for event in day_ahead[:8]
            ],
        )
    )
    lines.extend(
        _render_section(
            "Due in next 72h",
            [
                f"- {item.get('title', 'Untitled')} ({_display_timestamp(item.get('due_at'))})"
                for item in due_next_72h[:5]
            ],
        )
    )
    if provider_status:
        lines.extend(
            _render_section(
                "Calendar providers",
                [f"- {provider}: {status}" for provider, status in provider_status],
            )
        )

    return {"subject": subject, "body": "\n".join(lines).strip()}


def format_attention_weekly_digest_email(payload: dict) -> dict[str, str]:
    """Render a plain-text Monday weekly + day-ahead digest for email delivery."""
    digest_type = payload.get("digest_type") or "weekly_digest"
    subject = "Helionyx Weekly Digest"
    if digest_type == "monday_weekly_day_ahead":
        subject = "Helionyx Monday Weekly + Day-Ahead Digest"

    weekly_lookahead = payload.get("weekly_lookahead") or []
    day_ahead = payload.get("day_ahead") or []
    top_actionable = payload.get("top_actionable") or []
    calendar = payload.get("calendar") or {}

    lines = [subject, "=" * len(subject), ""]
    lines.extend(
        _render_section(
            "Weekly lookahead",
            [
                f"- {item.get('title', 'Untitled')} ({_display_timestamp(item.get('due_at'))})"
                for item in weekly_lookahead[:8]
            ],
        )
    )
    lines.extend(
        _render_section(
            "Today and next 24h schedule",
            [
                f"- {event.get('title', 'Untitled')} ({_display_timestamp(event.get('starts_at'))})"
                for event in day_ahead[:8]
            ],
        )
    )
    lines.extend(
        _render_section(
            "Top actionable tasks",
            [
                f"- {item.get('title', 'Untitled')} [{item.get('priority', 'p2')}]"
                for item in top_actionable[:5]
            ],
        )
    )

    provider_status = calendar.get("provider_status") or {}
    if provider_status:
        lines.extend(
            _render_section(
                "Calendar providers",
                [f"- {provider}: {status}" for provider, status in provider_status.items()],
            )
        )

    warnings = calendar.get("warnings") or []
    if warnings:
        lines.extend(
            _render_section("Calendar warnings", [f"- {warning}" for warning in warnings[:5]])
        )

    return {"subject": subject, "body": "\n".join(lines).strip()}
