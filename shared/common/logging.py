"""Logging configuration for Helionyx."""

import logging
import re
import sys


class SecretRedactionFilter(logging.Filter):
    """Best-effort redaction of secrets from log messages.

    This is not a perfect DLP system; it is a pragmatic baseline to prevent
    accidental leakage of common token/key patterns.
    """

    _patterns: list[tuple[re.Pattern[str], str]] = [
        # OpenAI-style keys (example: sk-...)
        (re.compile(r"sk-[A-Za-z0-9]{10,}"), "sk-***REDACTED***"),
        # Telegram bot token pattern: digits ':' base64-ish
        (re.compile(r"\b\d{5,}:[A-Za-z0-9_-]{20,}\b"), "***REDACTED_TELEGRAM_TOKEN***"),
        # Common env var key-value shapes
        (
            re.compile(
                r"\b(OPENAI_API_KEY|TELEGRAM_BOT_TOKEN|TELEGRAM_CHAT_ID)\s*=\s*([^\s,;]+)"
            ),
            r"\1=***REDACTED***",
        ),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:
            return True

        redacted = message
        for pattern, replacement in self._patterns:
            redacted = pattern.sub(replacement, redacted)

        # Overwrite the formatted message to avoid leaking secrets via args.
        record.msg = redacted
        record.args = ()
        return True


def setup_logging(level: str = "INFO"):
    """Configure application-wide logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Best-effort secret redaction on all handlers
    root = logging.getLogger()
    for handler in root.handlers:
        handler.addFilter(SecretRedactionFilter())

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)
