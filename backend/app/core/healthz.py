"""Deep health probe (Phase MVP-7).

Exposes `/healthz` — a single endpoint a load-balancer or uptime monitor can
hit to decide whether to send traffic. Returns 200 when every check passes,
503 when any check fails. Always returns a JSON body listing every check
result so an operator can `curl /healthz` and see which subsystem is sick
without opening a log file.

Checks:
- `database` — `SELECT 1` against the configured DB. Hard fail.
- `market_data_freshness` — newest `market_bars` row is younger than the
  configured threshold (default 7 days for weekend tolerance). Soft fail —
  the service can still serve UI from cache; degraded but not down.
- `recent_recommendation` — at least one recommendation in the last 30 days.
  Informational only; absence is normal in a fresh tenant.

Each check is short-circuited on exception so one broken check can't take the
whole probe out.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.ingestion import MarketBar
from app.models.recommendation import Recommendation

router = APIRouter()


# How stale market bars can be before we report degraded. Weekly bars +
# weekends mean 7d is the right tolerance for daily-bar ingestion; tune
# downward as we ingest higher-frequency data.
MARKET_DATA_STALE_AFTER = timedelta(days=7)
RECOMMENDATION_STALE_AFTER = timedelta(days=30)


@dataclass
class CheckResult:
    name: str
    ok: bool
    severity: str  # "hard" | "soft" | "info"
    detail: str


async def _check_database(db: AsyncSession) -> CheckResult:
    try:
        await db.execute(text("SELECT 1"))
        return CheckResult("database", True, "hard", "connected")
    except Exception as exc:
        # No traceback leak — just the class name.
        return CheckResult("database", False, "hard", f"{type(exc).__name__}")


async def _check_market_data_freshness(db: AsyncSession) -> CheckResult:
    try:
        newest = (await db.execute(
            select(func.max(MarketBar.bar_date))
        )).scalar_one_or_none()
        if newest is None:
            return CheckResult(
                "market_data_freshness", False, "soft", "no_market_bars_ingested"
            )
        now = datetime.now(UTC).date()
        age = now - newest
        if age > MARKET_DATA_STALE_AFTER:
            return CheckResult(
                "market_data_freshness", False, "soft",
                f"newest_bar_{newest.isoformat()}_age_{age.days}d",
            )
        return CheckResult(
            "market_data_freshness", True, "soft",
            f"newest_bar_{newest.isoformat()}",
        )
    except Exception as exc:
        return CheckResult("market_data_freshness", False, "soft", f"{type(exc).__name__}")


async def _check_recent_recommendation(db: AsyncSession) -> CheckResult:
    try:
        latest = (await db.execute(
            select(func.max(Recommendation.created_at))
        )).scalar_one_or_none()
        if latest is None:
            return CheckResult(
                "recent_recommendation", True, "info", "none_yet"
            )
        if latest.tzinfo is None:
            latest = latest.replace(tzinfo=UTC)
        age = datetime.now(UTC) - latest
        if age > RECOMMENDATION_STALE_AFTER:
            return CheckResult(
                "recent_recommendation", True, "info",
                f"latest_{latest.isoformat()}_age_{age.days}d",
            )
        return CheckResult(
            "recent_recommendation", True, "info",
            f"latest_{latest.isoformat()}",
        )
    except Exception as exc:
        return CheckResult("recent_recommendation", False, "info", f"{type(exc).__name__}")


def _http_status(results: list[CheckResult]) -> int:
    """503 only on hard-failing checks. Soft failures are reported but 200."""
    for r in results:
        if not r.ok and r.severity == "hard":
            return 503
    return 200


def _envelope(results: list[CheckResult]) -> dict[str, Any]:
    any_soft_fail = any(not r.ok and r.severity == "soft" for r in results)
    all_hard_ok = all(r.ok for r in results if r.severity == "hard")
    overall = "ok"
    if not all_hard_ok:
        overall = "unhealthy"
    elif any_soft_fail:
        overall = "degraded"
    return {
        "status": overall,
        "version": settings.app_version,
        "checks": [
            {
                "name": r.name,
                "ok": r.ok,
                "severity": r.severity,
                "detail": r.detail,
            }
            for r in results
        ],
    }


@router.get("/healthz")
async def healthz(response: Response, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Deep health probe. Always returns JSON; status code reflects hard checks."""
    results = [
        await _check_database(db),
        await _check_market_data_freshness(db),
        await _check_recent_recommendation(db),
    ]
    response.status_code = _http_status(results)
    return _envelope(results)
