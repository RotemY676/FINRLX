"""Phase OP-3 — notifications service.

Two adapters that conform to a simple ``NotificationChannel`` protocol:

  * ``WebhookChannel``  — POST JSON to ``NOTIFY_WEBHOOK_URL``
  * ``SmtpChannel``     — send email via ``NOTIFY_SMTP_*`` env vars

``notify_unsent_incidents(db, channels)`` walks open incidents and
sends one notification per (incident, channel) that hasn't been sent
before. The ``notifications`` table's UNIQUE constraint on
(incident_id, channel) makes this idempotent at the DB level too.

Both adapters fail-closed: any send error is logged into the
``Notification.status='failed'`` row with the exception message so a
future run can retry by deleting the failed row (manual operator
action; we don't auto-retry to avoid storms).
"""
from __future__ import annotations

import os
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.ops import Incident


class NotificationChannel(Protocol):
    name: str
    is_configured: bool

    async def send(self, subject: str, body: str) -> None: ...


@dataclass
class WebhookChannel:
    name: str = "webhook"

    @property
    def is_configured(self) -> bool:
        return bool(os.environ.get("NOTIFY_WEBHOOK_URL"))

    async def send(self, subject: str, body: str) -> None:
        url = os.environ.get("NOTIFY_WEBHOOK_URL")
        if not url:
            raise RuntimeError("NOTIFY_WEBHOOK_URL not configured")
        timeout = float(os.environ.get("NOTIFY_WEBHOOK_TIMEOUT_S", "10"))
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                url,
                json={"subject": subject, "body": body, "source": "finrlx"},
            )
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"webhook {resp.status_code}: {resp.text[:200]}"
                )


@dataclass
class SmtpChannel:
    name: str = "smtp"

    @property
    def is_configured(self) -> bool:
        host = os.environ.get("NOTIFY_SMTP_HOST")
        from_addr = os.environ.get("NOTIFY_SMTP_FROM")
        to_addr = os.environ.get("NOTIFY_SMTP_TO")
        return bool(host and from_addr and to_addr)

    async def send(self, subject: str, body: str) -> None:
        host = os.environ.get("NOTIFY_SMTP_HOST")
        port = int(os.environ.get("NOTIFY_SMTP_PORT", "587"))
        user = os.environ.get("NOTIFY_SMTP_USER")
        password = os.environ.get("NOTIFY_SMTP_PASSWORD")
        from_addr = os.environ.get("NOTIFY_SMTP_FROM")
        to_addr = os.environ.get("NOTIFY_SMTP_TO")

        if not (host and from_addr and to_addr):
            raise RuntimeError("NOTIFY_SMTP_HOST/FROM/TO required")

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg.set_content(body)

        # SMTP is sync; this whole adapter runs in a thread executor when
        # called inside an async pipeline, but for simplicity we call it
        # synchronously here (the notify job is daily, not request-path).
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port) as smtp:
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.ehlo()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)


def discover_channels() -> list[NotificationChannel]:
    """Return only the channels that have their config present."""
    return [c for c in (WebhookChannel(), SmtpChannel()) if c.is_configured]


def _format_incident_body(incident: Incident) -> str:
    return (
        f"Severity {incident.severity} — {incident.title}\n\n"
        f"Source: {incident.source or 'unknown'}\n"
        f"Status: {incident.status}\n\n"
        f"{incident.description or '(no description)'}"
    )


async def notify_unsent_incidents(
    db: AsyncSession,
    channels: list[NotificationChannel] | None = None,
) -> dict[str, int]:
    """Send notifications for incidents that don't have one per channel yet.

    Returns ``{sent, skipped, failed}`` counts.
    """
    channels = channels if channels is not None else discover_channels()
    if not channels:
        # Nothing configured — return early without touching the DB.
        return {"sent": 0, "skipped": 0, "failed": 0, "no_channels": 1}

    # Pull every open or recently-opened incident.
    incidents = (
        await db.execute(
            select(Incident).where(Incident.status == "open")
        )
    ).scalars().all()
    if not incidents:
        return {"sent": 0, "skipped": 0, "failed": 0}

    # Pre-fetch all existing notification (incident_id, channel) pairs.
    existing_rows = (
        await db.execute(
            select(Notification.incident_id, Notification.channel)
        )
    ).all()
    existing = {(row.incident_id, row.channel) for row in existing_rows}

    sent = 0
    skipped = 0
    failed = 0

    for incident in incidents:
        body = _format_incident_body(incident)
        subject = f"[FINRLX/{incident.severity}] {incident.title[:140]}"
        for channel in channels:
            key = (incident.id, channel.name)
            if key in existing:
                skipped += 1
                continue
            row = Notification(
                incident_id=incident.id,
                channel=channel.name,
                status="sent",
                subject=subject,
                body_preview=body[:500],
            )
            try:
                await channel.send(subject, body)
                sent += 1
            except Exception as exc:  # noqa: BLE001 — we want every error
                row.status = "failed"
                row.error = str(exc)[:2000]
                failed += 1
            db.add(row)

    await db.commit()
    return {"sent": sent, "skipped": skipped, "failed": failed}
