"""Phase MVP-8 — `scripts.manage_allowlist` CLI tests.

We exercise the async functions directly (not via subprocess) so the
in-memory test DB from conftest is reachable. Each test starts with the
seed allowlist empty (the conftest seed doesn't add allowlist rows).
"""
from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.auth import EmailAllowlist, RefreshToken, User
from scripts import manage_allowlist
from tests.conftest import test_session_factory


@pytest.mark.asyncio
async def test_add_inserts_and_normalizes_email(capsys):
    async with test_session_factory() as db:
        await manage_allowlist._add(db, "  Foo@Example.COM  ", note="cohort-A")

    async with test_session_factory() as db:
        row = (await db.execute(
            select(EmailAllowlist).where(EmailAllowlist.email == "foo@example.com")
        )).scalar_one_or_none()
        assert row is not None
        assert row.note == "cohort-A"


@pytest.mark.asyncio
async def test_add_is_idempotent(capsys):
    async with test_session_factory() as db:
        await manage_allowlist._add(db, "bar@example.com", note=None)
    async with test_session_factory() as db:
        await manage_allowlist._add(db, "bar@example.com", note="duplicate")
    out = capsys.readouterr().out
    assert "already-allowlisted" in out

    async with test_session_factory() as db:
        rows = (await db.execute(
            select(EmailAllowlist).where(EmailAllowlist.email == "bar@example.com")
        )).scalars().all()
        assert len(rows) == 1
        # Note from the first add wins; the second add is a no-op.
        assert rows[0].note is None


@pytest.mark.asyncio
async def test_remove_email(capsys):
    async with test_session_factory() as db:
        await manage_allowlist._add(db, "rm@example.com", note=None)
    async with test_session_factory() as db:
        await manage_allowlist._remove(db, "rm@example.com")
    async with test_session_factory() as db:
        row = (await db.execute(
            select(EmailAllowlist).where(EmailAllowlist.email == "rm@example.com")
        )).scalar_one_or_none()
        assert row is None


@pytest.mark.asyncio
async def test_remove_silent_when_not_present(capsys):
    async with test_session_factory() as db:
        await manage_allowlist._remove(db, "neverhere@example.com")
    out = capsys.readouterr().out
    assert "not-on-allowlist" in out


@pytest.mark.asyncio
async def test_deactivate_user_and_revoke_tokens(capsys):
    from datetime import UTC, datetime, timedelta

    async with test_session_factory() as db:
        # Create a user + an active refresh token.
        user = User(
            email="dx@example.com",
            password_hash="$2b$12$test_hash_only_for_test_value",
            is_active=True,
            role="user",
        )
        db.add(user)
        await db.flush()
        db.add(RefreshToken(
            user_id=user.id,
            token_hash="dummyhash",
            expires_at=datetime.now(UTC) + timedelta(days=1),
        ))
        await db.commit()

    async with test_session_factory() as db:
        await manage_allowlist._deactivate(db, "DX@example.com")

    async with test_session_factory() as db:
        u = (await db.execute(select(User).where(User.email == "dx@example.com"))).scalar_one()
        assert u.is_active is False
        tokens = (await db.execute(
            select(RefreshToken).where(RefreshToken.user_id == u.id)
        )).scalars().all()
        assert tokens
        assert all(t.revoked_at is not None for t in tokens)
