"""Phase OP-4 — rotate JWT_SECRET safely.

What this script does:

  1. Reads ``JWT_SECRET`` from env or prints how to set a fresh one.
  2. Revokes EVERY existing RefreshToken (so all sessions terminate
     immediately — the old token never accepts a new refresh).
  3. Logs an AuditEvent of the rotation.

The JWT secret itself is rotated **out of band** by the operator
(set the new value in Railway env vars, then redeploy). This script
is the in-app cleanup that prevents long-lived sessions from quietly
surviving the rotation.

Run:
    python -m scripts.rotate_jwt_secret --confirm
"""
from __future__ import annotations

import argparse
import asyncio
import secrets
from datetime import UTC, datetime

from sqlalchemy import select, update

from app.core.database import async_session_factory
from app.models.auth import RefreshToken
from app.models.ops import AuditEvent


async def _revoke_all_refresh_tokens(triggered_by: str) -> int:
    now = datetime.now(UTC)
    async with async_session_factory() as db:
        revoked_now = (
            await db.execute(
                update(RefreshToken)
                .where(RefreshToken.revoked_at.is_(None))
                .values(revoked_at=now)
            )
        ).rowcount or 0

        db.add(
            AuditEvent(
                actor="jwt_rotation",
                action="rotate_jwt_secret",
                object_type="auth",
                details={
                    "triggered_by": triggered_by,
                    "tokens_revoked": int(revoked_now),
                },
                occurred_at=now,
            )
        )
        await db.commit()
        return int(revoked_now)


def _dump_new_secret() -> str:
    """Generate a fresh 64-byte URL-safe random secret."""
    return secrets.token_urlsafe(48)


async def _count_active_tokens() -> int:
    async with async_session_factory() as db:
        rows = (
            await db.execute(
                select(RefreshToken).where(RefreshToken.revoked_at.is_(None))
            )
        ).scalars().all()
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Revoke all refresh tokens to invalidate sessions after JWT_SECRET rotation.",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually revoke. Without this flag we only report what would happen.",
    )
    parser.add_argument(
        "--triggered-by",
        default="manual-cli",
        help="Audit field — who/what triggered this rotation.",
    )
    parser.add_argument(
        "--print-new-secret",
        action="store_true",
        help="Print a fresh JWT_SECRET candidate to stdout (does not set it).",
    )
    args = parser.parse_args()

    if args.print_new_secret:
        print("Suggested new JWT_SECRET (set this in Railway env vars):")
        print(f"  {_dump_new_secret()}")

    active = asyncio.run(_count_active_tokens())
    print(f"Active refresh tokens (currently not revoked): {active}")

    if not args.confirm:
        print(
            "Dry run (no --confirm). After setting JWT_SECRET in Railway, "
            f"re-run with --confirm to revoke {active} active sessions."
        )
        return

    revoked = asyncio.run(_revoke_all_refresh_tokens(args.triggered_by))
    print(f"Revoked {revoked} refresh tokens. All users must re-login.")


if __name__ == "__main__":
    main()
