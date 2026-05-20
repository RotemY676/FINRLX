"""CLI to manage the FINRLX email allowlist (Phase MVP-8).

The allowlist gates signup. Each tester's email must be added BEFORE they
try `/auth/signup`, otherwise the request returns 403 with a generic
"invite-only" message.

Usage:
    python -m scripts.manage_allowlist add <email> [--note "Cohort A"]
    python -m scripts.manage_allowlist remove <email>
    python -m scripts.manage_allowlist list
    python -m scripts.manage_allowlist deactivate <email>     # also revokes refresh tokens

Connects via DATABASE_URL (same as the app). Safe to run against
production — every mutation prints a one-line audit summary.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.auth import EmailAllowlist, RefreshToken, User


def _normalize(email: str) -> str:
    return email.strip().lower()


async def _add(db: AsyncSession, email: str, note: str | None) -> None:
    e = _normalize(email)
    existing = await db.execute(select(EmailAllowlist).where(EmailAllowlist.email == e))
    if existing.scalar_one_or_none():
        print(f"already-allowlisted: {e}")
        return
    db.add(EmailAllowlist(email=e, note=note))
    await db.commit()
    print(f"added: {e}{' (' + note + ')' if note else ''}")


async def _remove(db: AsyncSession, email: str) -> None:
    e = _normalize(email)
    row = (await db.execute(select(EmailAllowlist).where(EmailAllowlist.email == e))).scalar_one_or_none()
    if row is None:
        print(f"not-on-allowlist: {e}")
        return
    await db.delete(row)
    await db.commit()
    print(f"removed: {e}")


async def _deactivate(db: AsyncSession, email: str) -> None:
    """Remove the email from the allowlist, deactivate the user, and revoke all refresh tokens."""
    e = _normalize(email)
    user = (await db.execute(select(User).where(User.email == e))).scalar_one_or_none()
    if user is None:
        print(f"no-such-user: {e}")
        await _remove(db, email)
        return
    user.is_active = False
    now = datetime.now(UTC)
    tokens = (await db.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
    )).scalars().all()
    for t in tokens:
        t.revoked_at = now
    allow = (await db.execute(select(EmailAllowlist).where(EmailAllowlist.email == e))).scalar_one_or_none()
    if allow is not None:
        await db.delete(allow)
    await db.commit()
    print(f"deactivated: {e} (user.is_active=False, revoked={len(tokens)} refresh tokens, removed from allowlist)")


async def _list(db: AsyncSession) -> None:
    rows = (await db.execute(select(EmailAllowlist).order_by(EmailAllowlist.email))).scalars().all()
    if not rows:
        print("(empty)")
        return
    for r in rows:
        suffix = f"  # {r.note}" if r.note else ""
        print(f"{r.email}{suffix}")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="manage_allowlist")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="add an email")
    p_add.add_argument("email")
    p_add.add_argument("--note", default=None)

    p_rm = sub.add_parser("remove", help="remove an email")
    p_rm.add_argument("email")

    sub.add_parser("list", help="list all allowlisted emails")

    p_deact = sub.add_parser("deactivate", help="deactivate user, revoke refresh tokens, remove from allowlist")
    p_deact.add_argument("email")

    return p


async def _run(argv: list[str]) -> int:
    args = _build_parser().parse_args(argv)
    async with async_session_factory() as db:
        if args.cmd == "add":
            await _add(db, args.email, args.note)
        elif args.cmd == "remove":
            await _remove(db, args.email)
        elif args.cmd == "list":
            await _list(db)
        elif args.cmd == "deactivate":
            await _deactivate(db, args.email)
    return 0


def main() -> int:
    return asyncio.run(_run(sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())
