"""Program LEAP S8 — background dossier refresh + material-change detection
(decision D38).

Runs inside the daily DAG:

  refresh_dossiers(db, budget)   For every persisted dossier touched within
                                 RETENTION_DAYS, rebuild when it is stale
                                 (new session available per the F2 calendar,
                                 or config version changed). Budget-aware:
                                 oldest-first, at most `budget` rebuilds per
                                 run; the skipped set is reported honestly.

  Material change rules (D38): regime flip, tournament winner change, or
  research-stance change between the previous and fresh dossier opens a
  severity-3 incident whose description links the dossier evidence
  (GS8.3: no notification without a dossier-linked evidence reference).
  The existing daily_notify_incidents job then delivers it through the
  configured channels — reusing, not duplicating, the notification path.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.autopilot import AutopilotDossier
from app.models.ops import Incident
from app.services.autopilot import CONFIG_VERSION
from app.services.autopilot_store import get_or_build_dossier
from app.utils import trading_calendar

logger = logging.getLogger(__name__)

RETENTION_DAYS = 30
DEFAULT_REFRESH_BUDGET = 10
INCIDENT_TITLE_PREFIX = "Dossier material change: "

__all__ = [
    "RefreshReport",
    "material_changes",
    "refresh_dossiers",
    "INCIDENT_TITLE_PREFIX",
]


@dataclass
class RefreshReport:
    evaluated: int = 0
    refreshed: list[str] = field(default_factory=list)
    skipped_fresh: list[str] = field(default_factory=list)
    skipped_budget: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)
    material_change_incidents: int = 0


def _needs_refresh(row: AutopilotDossier, now: datetime) -> bool:
    if row.config_version != CONFIG_VERSION:
        return True
    expected = trading_calendar.expected_latest_session(now).isoformat()
    return (row.latest_bar_date or "") < expected


def material_changes(old: dict, new: dict) -> list[dict]:
    """D38 rules, computed not editorialized. Each change carries before/after."""
    changes: list[dict] = []
    o_sum, n_sum = old.get("summary", {}) or {}, new.get("summary", {}) or {}
    if o_sum.get("regime") != n_sum.get("regime"):
        changes.append({"rule": "regime_flip",
                        "before": o_sum.get("regime"), "after": n_sum.get("regime")})
    if o_sum.get("stance") != n_sum.get("stance"):
        changes.append({"rule": "stance_change",
                        "before": o_sum.get("stance"), "after": n_sum.get("stance")})

    def _winner(d: dict):
        w = ((d.get("sections", {}) or {}).get("model_insight", {}) or {}).get("winner") or {}
        return w.get("key")

    if _winner(old) != _winner(new):
        changes.append({"rule": "tournament_winner_change",
                        "before": _winner(old), "after": _winner(new)})
    return changes


async def _open_change_incident(
    db: AsyncSession, ticker: str, changes: list[dict], new: dict
) -> bool:
    """One open incident per ticker at a time; idempotent like the watchdogs."""
    title = f"{INCIDENT_TITLE_PREFIX}{ticker}"
    existing = (
        await db.execute(
            select(Incident).where(Incident.title == title, Incident.status != "resolved")
        )
    ).scalar_one_or_none()
    if existing is not None:
        return False
    evidence_ref = (
        f"/api/v1/autopilot/dossier?ticker={ticker} "
        f"(latest bar {(new.get('freshness') or {}).get('latest_bar')}, "
        f"config {new.get('config_version')})"
    )
    db.add(
        Incident(
            title=title,
            severity=3,
            status="open",
            source="autopilot_refresh",
            description=(
                f"Automatic re-analysis of {ticker} detected: "
                + "; ".join(
                    f"{c['rule']} ({c['before']} -> {c['after']})" for c in changes
                )
                + f". Evidence: {evidence_ref}. Research analysis, not advice."
            ),
        )
    )
    await db.flush()
    return True


async def refresh_dossiers(
    db: AsyncSession,
    budget: int = DEFAULT_REFRESH_BUDGET,
    now: datetime | None = None,
) -> RefreshReport:
    now = now or datetime.now(UTC)
    report = RefreshReport()
    cutoff = now - timedelta(days=RETENTION_DAYS)
    rows = (
        (
            await db.execute(
                select(AutopilotDossier)
                .where(AutopilotDossier.generated_at >= cutoff)
                .order_by(AutopilotDossier.generated_at.asc())  # oldest-first (D38)
            )
        )
        .scalars()
        .all()
    )
    report.evaluated = len(rows)
    for row in rows:
        if not _needs_refresh(row, now):
            report.skipped_fresh.append(row.ticker)
            continue
        if len(report.refreshed) >= budget:
            report.skipped_budget.append(row.ticker)
            continue
        try:
            old = json.loads(row.payload_json)
            fresh = await get_or_build_dossier(db, row.ticker)
            report.refreshed.append(row.ticker)
            changes = material_changes(old, fresh)
            if changes and await _open_change_incident(db, row.ticker, changes, fresh):
                report.material_change_incidents += 1
        except (ValueError, RuntimeError) as exc:
            report.failed[row.ticker] = str(exc)[:200]
            logger.warning("dossier refresh failed for %s: %s", row.ticker, exc)
    return report
