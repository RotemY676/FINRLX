"""Program LEAP F1.5 — equity price freshness watchdog (decision D6).

Generalizes the fx_freshness pattern to market_bars: per ticker, how many
trading days is the latest ingested bar behind the latest expected session,
classified as:

    fresh     lag <= 1 trading day
    stale     2 <= lag <= 5
    degraded  lag > 5

Session arithmetic is delegated to app.utils.trading_calendar (F2), so
holidays are handled correctly; if the calendar package is unavailable the
utility degrades to weekday logic by itself.

Pure analysis (evaluate_price_freshness) + idempotent incident emission,
mirroring fx_freshness so the OP-2 scheduler can call it safely.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingestion import MarketBar
from app.models.ops import Incident
from app.utils import trading_calendar

FRESH_MAX_LAG = 1
STALE_MAX_LAG = 5
INCIDENT_TITLE_PREFIX = "Price data degraded: "

__all__ = [
    "TickerFreshness",
    "PriceFreshnessReport",
    "evaluate_price_freshness",
    "emit_incidents_if_degraded",
    "classify_lag",
]


@dataclass(frozen=True)
class TickerFreshness:
    ticker: str
    latest_bar_date_iso: str
    lag_trading_days: int
    status: str  # fresh | stale | degraded


@dataclass
class PriceFreshnessReport:
    evaluated_at: datetime
    expected_latest_session_iso: str
    tickers: list[TickerFreshness] = field(default_factory=list)
    stale: list[TickerFreshness] = field(default_factory=list)
    degraded: list[TickerFreshness] = field(default_factory=list)


def _expected_latest_session(now: datetime) -> date:
    return trading_calendar.expected_latest_session(now)


def _trading_day_lag(latest: date, expected: date) -> int:
    return trading_calendar.trading_day_lag(latest, expected)


def classify_lag(lag: int) -> str:
    if lag <= FRESH_MAX_LAG:
        return "fresh"
    if lag <= STALE_MAX_LAG:
        return "stale"
    return "degraded"


async def evaluate_price_freshness(
    db: AsyncSession,
    now: datetime | None = None,
) -> PriceFreshnessReport:
    """Scan market_bars and report per-ticker freshness (unflagged bars only)."""
    now = now or datetime.now(UTC)
    expected = _expected_latest_session(now)
    report = PriceFreshnessReport(
        evaluated_at=now, expected_latest_session_iso=expected.isoformat()
    )
    rows = (
        await db.execute(
            select(MarketBar.ticker, func.max(MarketBar.bar_date))
            .where(MarketBar.quality_flag.is_(None))
            .group_by(MarketBar.ticker)
        )
    ).all()
    for ticker, latest in rows:
        lag = _trading_day_lag(latest, expected)
        tf = TickerFreshness(
            ticker=ticker,
            latest_bar_date_iso=latest.isoformat(),
            lag_trading_days=lag,
            status=classify_lag(lag),
        )
        report.tickers.append(tf)
        if tf.status == "stale":
            report.stale.append(tf)
        elif tf.status == "degraded":
            report.degraded.append(tf)
    return report


async def emit_incidents_if_degraded(
    db: AsyncSession, report: PriceFreshnessReport
) -> int:
    """Persist one open incident per degraded ticker; idempotent by title."""
    emitted = 0
    for tf in report.degraded:
        title = f"{INCIDENT_TITLE_PREFIX}{tf.ticker}"
        existing = (
            await db.execute(
                select(Incident).where(
                    Incident.title == title, Incident.status != "resolved"
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue
        db.add(
            Incident(
                title=title,
                severity=2,
                status="open",
                source="price_freshness",
                description=(
                    f"Latest unflagged bar {tf.latest_bar_date_iso}; "
                    f"lag {tf.lag_trading_days} trading day(s); "
                    f"expected session {report.expected_latest_session_iso}."
                ),
            )
        )
        emitted += 1
    if emitted:
        await db.flush()
    return emitted
