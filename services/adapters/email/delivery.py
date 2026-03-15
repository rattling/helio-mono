"""SMTP delivery adapter for digest emails."""

from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage
from typing import Any


def _send_email_sync(
    *,
    host: str,
    port: int,
    username: str | None,
    password: str | None,
    from_address: str,
    to_address: str,
    subject: str,
    body: str,
    use_tls: bool,
) -> dict[str, Any]:
    message = EmailMessage()
    message["From"] = from_address
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.ehlo()
        if use_tls:
            smtp.starttls()
            smtp.ehlo()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(message)

    return {
        "sent": True,
        "recipient": to_address,
        "subject": subject,
    }


async def send_email_smtp(
    *,
    host: str,
    port: int,
    username: str | None,
    password: str | None,
    from_address: str,
    to_address: str,
    subject: str,
    body: str,
    use_tls: bool = True,
) -> dict[str, Any]:
    """Send a plain-text digest email via SMTP using a deterministic adapter."""
    return await asyncio.to_thread(
        _send_email_sync,
        host=host,
        port=port,
        username=username,
        password=password,
        from_address=from_address,
        to_address=to_address,
        subject=subject,
        body=body,
        use_tls=use_tls,
    )
