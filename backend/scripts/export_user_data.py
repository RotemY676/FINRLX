"""Phase OP-4 — GDPR-style per-user data export.

Bundles everything FINRLX knows about one user — profile (current +
revisions), paper portfolios, audit events — into a single JSON blob.

Run:
    python -m scripts.export_user_data --email someone@example.com > export.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from typing import Any

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.auth import User
from app.models.ops import AuditEvent
from app.models.profile import InvestorProfile, InvestorProfileRevision
from app.models.validation import PaperPortfolio


def _serialize(obj: Any) -> Any:
    """Best-effort serializer for SQLAlchemy rows."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "__table__"):
        out = {}
        for col in obj.__table__.columns:
            value = getattr(obj, col.name)
            out[col.name] = _serialize(value)
        return out
    if isinstance(obj, list):
        return [_serialize(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


async def export_for_email(email: str) -> dict:
    async with async_session_factory() as db:
        user = (
            await db.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        if user is None:
            return {"error": f"no user found for email={email!r}"}

        profile = (
            await db.execute(
                select(InvestorProfile).where(InvestorProfile.user_id == user.id)
            )
        ).scalar_one_or_none()
        revisions = (
            await db.execute(
                select(InvestorProfileRevision)
                .where(InvestorProfileRevision.user_id == user.id)
                .order_by(InvestorProfileRevision.version.desc())
            )
        ).scalars().all()
        portfolios = (
            await db.execute(
                select(PaperPortfolio).where(PaperPortfolio.user_id == user.id)
            )
        ).scalars().all()
        # Audit events keyed by user id appear in details["user_id"] etc.;
        # we capture rows where the actor is the user's email or id.
        audits = (
            await db.execute(
                select(AuditEvent).where(AuditEvent.actor.in_((user.id, email)))
            )
        ).scalars().all()

    return {
        "exported_at": datetime.utcnow().isoformat(),
        "user": _serialize(user),
        "investor_profile": _serialize(profile),
        "profile_revisions": [_serialize(r) for r in revisions],
        "paper_portfolios": [_serialize(p) for p in portfolios],
        "audit_events": [_serialize(a) for a in audits],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export a user's profile + portfolios + audit events as JSON.",
    )
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    out = asyncio.run(export_for_email(args.email))
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
