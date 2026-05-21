"""Phase OP-3 — notifications service contract.

Coverage:
* discover_channels returns nothing when env vars missing
* Webhook adapter is_configured reads NOTIFY_WEBHOOK_URL
* SMTP adapter is_configured reads NOTIFY_SMTP_HOST + FROM + TO
* notify_unsent_incidents returns no_channels when nothing configured
* notify_unsent_incidents sends one row per (incident, channel) using
  a stub channel
* notify_unsent_incidents idempotent: second run for the same incident
  is "skipped"
* notify_unsent_incidents captures failure into status=failed
* daily_notify_incidents job key is in DAILY_DAG (DAG contract)
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest
from sqlalchemy import delete, select

from app.jobs.daily_dag import DAILY_DAG
from app.models.notification import Notification
from app.models.ops import Incident
from app.services.notifications import (
    SmtpChannel,
    WebhookChannel,
    discover_channels,
    notify_unsent_incidents,
)


@dataclass
class _StubChannel:
    name: str = "stub"
    is_configured: bool = True
    sent: list[tuple[str, str]] | None = None
    should_fail: bool = False

    def __post_init__(self):
        if self.sent is None:
            self.sent = []

    async def send(self, subject: str, body: str) -> None:
        if self.should_fail:
            raise RuntimeError("stub failure")
        assert self.sent is not None
        self.sent.append((subject, body))


async def _purge_test_notifications(db) -> None:
    await db.execute(delete(Notification))
    # purge incidents we'll insert in this test
    await db.execute(delete(Incident).where(Incident.source == "op3_test"))
    await db.commit()


def test_webhook_unconfigured_by_default(monkeypatch):
    monkeypatch.delenv("NOTIFY_WEBHOOK_URL", raising=False)
    ch = WebhookChannel()
    assert ch.is_configured is False


def test_webhook_configured_when_env_set(monkeypatch):
    monkeypatch.setenv("NOTIFY_WEBHOOK_URL", "https://example.com/hook")
    ch = WebhookChannel()
    assert ch.is_configured is True


def test_smtp_unconfigured_when_missing_env(monkeypatch):
    monkeypatch.delenv("NOTIFY_SMTP_HOST", raising=False)
    ch = SmtpChannel()
    assert ch.is_configured is False


def test_smtp_configured_with_full_env(monkeypatch):
    monkeypatch.setenv("NOTIFY_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("NOTIFY_SMTP_FROM", "noreply@example.com")
    monkeypatch.setenv("NOTIFY_SMTP_TO", "ops@example.com")
    ch = SmtpChannel()
    assert ch.is_configured is True


def test_discover_channels_returns_none_when_nothing_set(monkeypatch):
    for var in (
        "NOTIFY_WEBHOOK_URL", "NOTIFY_SMTP_HOST",
        "NOTIFY_SMTP_FROM", "NOTIFY_SMTP_TO",
    ):
        monkeypatch.delenv(var, raising=False)
    assert discover_channels() == []


@pytest.mark.asyncio
async def test_notify_returns_no_channels_when_nothing_set(monkeypatch):
    from tests.conftest import test_session_factory

    for var in (
        "NOTIFY_WEBHOOK_URL", "NOTIFY_SMTP_HOST",
        "NOTIFY_SMTP_FROM", "NOTIFY_SMTP_TO",
    ):
        monkeypatch.delenv(var, raising=False)
    async with test_session_factory() as db:
        result = await notify_unsent_incidents(db)
    assert result.get("no_channels") == 1


@pytest.mark.asyncio
async def test_notify_sends_one_row_per_incident_with_stub_channel():
    """Sends exactly one row per (open incident, channel) pair.

    The conftest pre-seeds one open Incident, so we assert the count
    matches the number of currently-open incidents — not a fixed 1.
    """
    from tests.conftest import test_session_factory

    stub = _StubChannel()
    async with test_session_factory() as db:
        await _purge_test_notifications(db)
        db.add(
            Incident(
                severity=2, title="OP-3 test incident", description="hi",
                status="open", source="op3_test",
            )
        )
        await db.commit()

        open_count = len(
            (await db.execute(select(Incident).where(Incident.status == "open")))
            .scalars()
            .all()
        )
        result = await notify_unsent_incidents(db, channels=[stub])
        rows = (await db.execute(select(Notification))).scalars().all()

    assert result["sent"] == open_count
    assert result["skipped"] == 0
    assert result["failed"] == 0
    assert len(stub.sent or []) == open_count
    assert len(rows) == open_count
    assert all(r.status == "sent" for r in rows)
    assert all(r.channel == "stub" for r in rows)


@pytest.mark.asyncio
async def test_notify_idempotent_on_second_run():
    from tests.conftest import test_session_factory

    stub = _StubChannel()
    async with test_session_factory() as db:
        await _purge_test_notifications(db)
        db.add(
            Incident(
                severity=2, title="OP-3 idempotent test", description="hi",
                status="open", source="op3_test",
            )
        )
        await db.commit()
        first = await notify_unsent_incidents(db, channels=[stub])
        second = await notify_unsent_incidents(db, channels=[stub])

    # Both runs cover the same set of incidents; second is fully idempotent.
    assert first["sent"] >= 1
    assert second["sent"] == 0
    assert second["skipped"] == first["sent"]


@pytest.mark.asyncio
async def test_notify_captures_failures():
    from tests.conftest import test_session_factory

    failing = _StubChannel(name="failing", should_fail=True)
    async with test_session_factory() as db:
        await _purge_test_notifications(db)
        db.add(
            Incident(
                severity=1, title="OP-3 failure test", description="x",
                status="open", source="op3_test",
            )
        )
        await db.commit()
        open_count = len(
            (await db.execute(select(Incident).where(Incident.status == "open")))
            .scalars()
            .all()
        )
        result = await notify_unsent_incidents(db, channels=[failing])

        rows = (
            await db.execute(select(Notification))
        ).scalars().all()

    assert result["failed"] == open_count
    assert result["sent"] == 0
    assert all(r.status == "failed" for r in rows)
    assert any("stub failure" in (r.error or "") for r in rows)


def test_notify_job_is_registered_in_dag():
    keys = [k for k, _ in DAILY_DAG]
    assert "daily_notify_incidents" in keys
