"""Tests for deterministic SMTP email delivery."""

from unittest.mock import MagicMock

import pytest

from services.adapters.email.delivery import send_email_smtp


@pytest.mark.asyncio
async def test_send_email_smtp_uses_tls_and_login(monkeypatch):
    smtp_instance = MagicMock()
    smtp_context = MagicMock()
    smtp_context.__enter__.return_value = smtp_instance
    smtp_context.__exit__.return_value = False
    smtp_factory = MagicMock(return_value=smtp_context)
    monkeypatch.setattr("services.adapters.email.delivery.smtplib.SMTP", smtp_factory)

    result = await send_email_smtp(
        host="smtp.gmail.com",
        port=587,
        username="ops@example.com",
        password="secret",
        from_address="ops@example.com",
        to_address="john@example.com",
        subject="Digest",
        body="Body",
        use_tls=True,
    )

    assert result["sent"] is True
    assert result["recipient"] == "john@example.com"
    smtp_factory.assert_called_once_with("smtp.gmail.com", 587, timeout=20)
    smtp_instance.starttls.assert_called_once()
    smtp_instance.login.assert_called_once_with("ops@example.com", "secret")
    smtp_instance.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_email_smtp_skips_login_without_credentials(monkeypatch):
    smtp_instance = MagicMock()
    smtp_context = MagicMock()
    smtp_context.__enter__.return_value = smtp_instance
    smtp_context.__exit__.return_value = False
    monkeypatch.setattr(
        "services.adapters.email.delivery.smtplib.SMTP",
        MagicMock(return_value=smtp_context),
    )

    await send_email_smtp(
        host="localhost",
        port=1025,
        username=None,
        password=None,
        from_address="ops@example.com",
        to_address="john@example.com",
        subject="Digest",
        body="Body",
        use_tls=False,
    )

    smtp_instance.starttls.assert_not_called()
    smtp_instance.login.assert_not_called()
    smtp_instance.send_message.assert_called_once()
