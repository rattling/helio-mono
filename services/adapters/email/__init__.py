"""Deterministic email rendering and delivery adapters for digest workflows."""

from services.adapters.email.delivery import send_email_smtp
from services.adapters.email.formatters import (
    format_attention_daily_digest_email,
    format_attention_weekly_digest_email,
)

__all__ = [
    "format_attention_daily_digest_email",
    "format_attention_weekly_digest_email",
    "send_email_smtp",
]
