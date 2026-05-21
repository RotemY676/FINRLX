"""Phase FX-4 — FX freshness watchdog.

Computes the lag in hours per ``(base, quote)`` pair from the most
recent ``fx_rates`` row and emits ``Incident`` rows when the lag
exceeds the threshold. Pure analysis + an idempotent emission step so
the once-per-hour OP-2 scheduler can call it without duplicate
incidents.

``evaluate_freshness`` returns the full report; ``emit_incidents_if_stale``
takes that report and persists incidents. Tests cover both ends in
isolation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fx import FxRate
from app.models.ops import Incident

DEFAULT_STALE_THRESHOLD_HOURS = 48
INCIDENT_TITLE_PREFIX = "FX stale: "


@dataclass(frozen=True)
class PairFreshness:
    base: str
    quote: str
    latest_rate_date_iso: str
    age_hours: float
    is_stale: bool


@dataclass
class FxFreshnessReport:
    evaluated_at: datetime
    threshold_hours: float
    pairs: list[PairFreshness] = field(default_factory=list)
    stale_pairs: list[PairFreshness] = field(default_factory=list)


async def evaluate_freshness(
    db: AsyncSession,
    threshold_hours: float = DEFAULT_STALE_THRESHOLD_HOURS,
    now: datetime | None = None,
) -> FxFreshnessReport:
    """Scan fx_rates and report per (base, quote) freshness.

    ``now`` defaults to ``datetime.now(UTC)``; pass an explicit value
    in tests to keep them deterministic.
    """
    now = now or datetime.now(UTC)
    rows = (
        await db.execute(
            select(FxRate.base_currency, FxRate.quote_currency, FxRate.rate_date)
        )
    ).all()

    latest_by_pair: dict[tuple[str, str], datetime] = {}
    for base, quote, rate_date in rows:
        # rate_date is a date; treat end-of-day UTC as the publish moment
        publish_dt = datetime(
            rate_date.year, rate_date.month, rate_date.day, tzinfo=UTC,
        ) + timedelta(hours=18)  # ECB publishes ~16:00 CET
        prev = latest_by_pair.get((base, quote))
        if prev is None or publish_dt > prev:
            latest_by_pair[(base, quote)] = publish_dt

    pairs: list[PairFreshness] = []
    stale: list[PairFreshness] = []
    for (base, quote), latest_dt in sorted(latest_by_pair.items()):
        age = (now - latest_dt).total_seconds() / 3600.0
        pf = PairFreshness(
            base=base,
            quote=quote,
            latest_rate_date_iso=latest_dt.date().isoformat(),
            age_hours=round(age, 1),
            is_stale=age > threshold_hours,
        )
        pairs.append(pf)
        if pf.is_stale:
            stale.append(pf)

    return FxFreshnessReport(
        evaluated_at=now,
        threshold_hours=threshold_hours,
        pairs=pairs,
        stale_pairs=stale,
    )


def _incident_title(p: PairFreshness) -> str:
    return f"{INCIDENT_TITLE_PREFIX}{p.base}->{p.quote} (lag {p.age_hours:.1f}h)"


def _severity_for(age_hours: float) -> int:
    """Translate age into 1-4 severity matching the rest of the codebase."""
    if age_hours <= 72:
        return 3   # warning
    if age_hours <= 168:
        return 2   # high
    return 1       # critical


async def emit_incidents_if_stale(
    db: AsyncSession, report: FxFreshnessReport
) -> dict[str, int]:
    """Open one Incident per stale pair, but only if no open one exists.

    Idempotent for the scheduler: re-running with the same report
    doesn't duplicate rows.

    Returns ``{"opened": N, "skipped_existing": M}``.
    """
    opened = 0
    skipped = 0

    # Pre-fetch open FX-stale incidents to avoid N+1 queries
    open_titles = set(
        (
            await db.execute(
                select(Incident.title)
                .where(Incident.status == "open")
                .where(Incident.title.like(f"{INCIDENT_TITLE_PREFIX}%"))
            )
        ).scalars().all()
    )

    for pair in report.stale_pairs:
        title = _incident_title(pair)
        # Match on the prefix + arrow pattern — not the lag number, which
        # changes each run. The "key" is base->quote.
        prefix = f"{INCIDENT_TITLE_PREFIX}{pair.base}->{pair.quote}"
        if any(t.startswith(prefix) for t in open_titles):
            skipped += 1
            continue

        db.add(
            Incident(
                severity=_severity_for(pair.age_hours),
                title=title,
                description=(
                    f"FX cache for {pair.base}->{pair.quote} has not been "
                    f"updated for {pair.age_hours:.1f}h (latest row: "
                    f"{pair.latest_rate_date_iso}). Run "
                    f"`python -m scripts.fx_freshness_watchdog` after "
                    f"diagnosing upstream."
                ),
                status="open",
                source="fx_freshness_watchdog",
            )
        )
        opened += 1
        # Record the just-added title so we don't open a second one this run
        # if the same pair shows up twice in stale_pairs (shouldn't happen
        # but defends against future grouping changes).
        open_titles.add(title)

    if opened:
        await db.commit()
    return {"opened": opened, "skipped_existing": skipped}
