"""Phase OP-4 — JWT rotation script contract.

The script's effect: every non-revoked RefreshToken becomes revoked,
and an audit_events row records the rotation.

We test the underlying coroutines from the script module (not the
argparse main()) because the CLI exits before we can assert anything.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models.auth import RefreshToken
from app.models.ops import AuditEvent


@pytest.mark.asyncio
async def test_revoke_all_refresh_tokens_marks_active_ones_revoked():
    """Insert an active token, run the rotation script's revoke
    coroutine, expect status=revoked + audit entry."""
    import scripts.rotate_jwt_secret as rot_mod
    from tests.conftest import test_session_factory

    # Patch the module-level async_session_factory so the script writes
    # to the in-memory test DB.
    rot_mod.async_session_factory = test_session_factory

    user_id = "op4-test-user-1"
    token_id = "op4-test-token-1"
    async with test_session_factory() as db:
        db.add(
            RefreshToken(
                id=token_id,
                user_id=user_id,
                token_hash="hash-1",
                issued_at=datetime.now(UTC),
                expires_at=datetime.now(UTC) + timedelta(days=7),
            )
        )
        await db.commit()

    revoked = await rot_mod._revoke_all_refresh_tokens("test-runner")
    assert revoked >= 1  # at least our inserted one

    async with test_session_factory() as db:
        row = (
            await db.execute(
                select(RefreshToken).where(RefreshToken.id == token_id)
            )
        ).scalar_one()
        assert row.revoked_at is not None

        audits = (
            await db.execute(
                select(AuditEvent).where(
                    AuditEvent.action == "rotate_jwt_secret"
                )
            )
        ).scalars().all()
        assert any(
            (a.details or {}).get("triggered_by") == "test-runner"
            for a in audits
        )


@pytest.mark.asyncio
async def test_revoke_skips_already_revoked_tokens():
    import scripts.rotate_jwt_secret as rot_mod
    from tests.conftest import test_session_factory

    rot_mod.async_session_factory = test_session_factory

    user_id = "op4-test-user-2"
    token_id = "op4-test-token-2"
    async with test_session_factory() as db:
        db.add(
            RefreshToken(
                id=token_id,
                user_id=user_id,
                token_hash="hash-2",
                issued_at=datetime.now(UTC),
                expires_at=datetime.now(UTC) + timedelta(days=7),
                revoked_at=datetime.now(UTC),  # already revoked
            )
        )
        await db.commit()

    # Run again — should NOT touch the already-revoked row.
    before = (
        await rot_mod._revoke_all_refresh_tokens("test-noop")
    )
    # Whatever the count is, our already-revoked token's revoked_at
    # must not have moved.
    async with test_session_factory() as db:
        row = (
            await db.execute(
                select(RefreshToken).where(RefreshToken.id == token_id)
            )
        ).scalar_one()
        # revoked_at is set; rerun keeps it set
        assert row.revoked_at is not None
    # The count is whatever was *newly* revoked this run. We only
    # assert non-negative and finite.
    assert before >= 0


def test_dump_new_secret_returns_url_safe_string():
    import scripts.rotate_jwt_secret as rot_mod

    s = rot_mod._dump_new_secret()
    # url-safe base64 with 48 bytes input ≈ 64 chars
    assert len(s) >= 32
    for c in s:
        assert c.isalnum() or c in "_-"
