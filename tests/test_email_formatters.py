"""Tests for digest email renderers."""

from services.adapters.email.formatters import (
    format_attention_daily_digest_email,
    format_attention_weekly_digest_email,
)


def test_format_attention_weekly_digest_email_monday_shape():
    result = format_attention_weekly_digest_email(
        {
            "digest_type": "monday_weekly_day_ahead",
            "weekly_lookahead": [{"title": "Ship milestone", "due_at": "2026-03-17T09:00:00"}],
            "day_ahead": [{"title": "Team Sync", "starts_at": "2026-03-16T10:00:00Z"}],
            "top_actionable": [{"title": "Review queue", "priority": "p0"}],
            "calendar": {"provider_status": {"google": "ok"}, "warnings": ["zoho:degraded"]},
        }
    )

    assert result["subject"] == "Helionyx Monday Weekly + Day-Ahead Digest"
    assert "Ship milestone" in result["body"]
    assert "Team Sync" in result["body"]
    assert "google: ok" in result["body"]
    assert "zoho:degraded" in result["body"]


def test_format_attention_daily_digest_email_weekday_shape():
    result = format_attention_daily_digest_email(
        {
            "digest_type": "weekday_day_ahead",
            "top_actionable": [{"title": "Review queue", "priority": "p0"}],
            "day_ahead": [{"title": "Customer Call", "starts_at": "2026-03-18T09:30:00Z"}],
            "due_next_72h": [{"title": "Ship milestone", "due_at": "2026-03-19T09:00:00"}],
            "calendar": {"provider_status": {"google": "ok", "zoho": "unconfigured"}},
        }
    )

    assert result["subject"] == "Helionyx Weekday Day-Ahead Digest"
    assert "Customer Call" in result["body"]
    assert "Ship milestone" in result["body"]
    assert "zoho: unconfigured" in result["body"]
