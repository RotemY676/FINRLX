"""Forward-scored track record (phase 7).

Determinism proves the same inputs give the same answer twice. It does not
prove the answer was any good. This module is the other half: record what was
claimed when it was claimed, then score it against what actually happened.

Honesty rules, all enforced by tests:
  * An observation is only scored once its horizon has genuinely elapsed and a
    real later bar exists. No interpolation, no "close enough" bar.
  * With too few scored observations the summary reports `insufficient_sample`
    and NO hit rate. A rate over three observations is noise wearing a
    percentage sign, and publishing it would be worse than publishing nothing.
  * Buckets with no data are omitted, never rendered as 0%.
"""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.track_record import StanceObservation

DEFAULT_HORIZON_DAYS = 21
# Below this, a hit rate is noise. Chosen as a stated convention and published
# in the payload so a reader can see the bar being applied.
MIN_SAMPLE_FOR_RATE = 20
# One observation per ticker per this window — a user refreshing a dossier ten
# times must not create ten "predictions" and inflate the sample.
DEDUPE_WINDOW = timedelta(hours=20)


async def record_stance(
    db: AsyncSession,
    *,
    ticker: str,
    stance: str,
    composite_score: float,
    observed_bar_date: date,
    observed_close: float,
    avg_confidence: float | None = None,
    uncertainty_tier: str | None = None,
    config_version: str | None = None,
    horizon_days: int = DEFAULT_HORIZON_DAYS,
    now: datetime | None = None,
) -> StanceObservation | None:
    """Record a served stance. Returns None if one already exists in-window.

    Deduplication is what keeps this a record of *claims* rather than a record
    of page views.
    """
    now = now or datetime.now(UTC)
    cutoff = now - DEDUPE_WINDOW
    existing = (await db.execute(
        select(StanceObservation)
        .where(StanceObservation.ticker == ticker)
        .where(StanceObservation.observed_at >= cutoff)
        .limit(1)
    )).scalar_one_or_none()
    if existing is not None:
        return None

    row = StanceObservation(
        ticker=ticker,
        stance=stance,
        composite_score=composite_score,
        avg_confidence=avg_confidence,
        uncertainty_tier=uncertainty_tier,
        config_version=config_version,
        observed_at=now,
        observed_bar_date=observed_bar_date,
        observed_close=observed_close,
        horizon_days=horizon_days,
    )
    db.add(row)
    await db.flush()
    return row


def _is_mature(row: StanceObservation, today: date) -> bool:
    return (today - row.observed_bar_date).days >= row.horizon_days


async def score_matured(
    db: AsyncSession,
    price_lookup,
    *,
    today: date | None = None,
) -> int:
    """Score observations whose horizon has elapsed. Returns how many scored.

    `price_lookup(ticker, on_or_after) -> (date, close) | None` supplies the
    outcome price. Returning None means the outcome is not yet observable, and
    the row is simply left unscored — an unscored row is honest, an imputed one
    is not.
    """
    today = today or datetime.now(UTC).date()
    rows = (await db.execute(
        select(StanceObservation).where(StanceObservation.scored_at.is_(None))
    )).scalars().all()

    scored = 0
    for row in rows:
        if not _is_mature(row, today):
            continue
        target = row.observed_bar_date + timedelta(days=row.horizon_days)
        found = price_lookup(row.ticker, target)
        if not found:
            continue
        out_date, out_close = found
        if out_close is None or row.observed_close in (None, 0):
            continue
        row.outcome_bar_date = out_date
        row.outcome_close = out_close
        row.realized_return = (out_close - row.observed_close) / row.observed_close
        row.scored_at = datetime.now(UTC)
        scored += 1
    return scored


def _directionally_right(stance: str, realized_return: float) -> bool | None:
    """Did the stance point the way the price went?

    A neutral stance makes no directional claim, so it is excluded from the hit
    rate rather than counted as a win or a loss — scoring it either way would
    manufacture a result from an absence of one.
    """
    s = (stance or "").lower()
    if s in {"buy", "constructive"}:
        return realized_return > 0
    if s in {"sell", "trim", "cautious"}:
        return realized_return < 0
    return None


async def track_record_summary(db: AsyncSession) -> dict:
    """Aggregate the forward record. Fails closed on a thin sample."""
    rows = (await db.execute(select(StanceObservation))).scalars().all()
    scored = [r for r in rows if r.scored_at is not None and r.realized_return is not None]
    directional = [
        (r, _directionally_right(r.stance, r.realized_return))
        for r in scored
    ]
    directional = [(r, hit) for r, hit in directional if hit is not None]

    summary: dict = {
        "observations_recorded": len(rows),
        "observations_scored": len(scored),
        "directional_observations": len(directional),
        "min_sample_for_rate": MIN_SAMPLE_FOR_RATE,
        "horizon_days": DEFAULT_HORIZON_DAYS,
        "kind": (
            "forward-scored record of stances as they were served — not a "
            "backtest, and not a forecast of future results"
        ),
    }

    if rows:
        first = min(r.observed_at for r in rows)
        summary["first_observation_at"] = first.isoformat()

    if len(directional) < MIN_SAMPLE_FOR_RATE:
        summary["status"] = "insufficient_sample"
        summary["hit_rate"] = None
        summary["note"] = (
            f"{len(directional)} directional observations scored; a hit rate is "
            f"withheld below {MIN_SAMPLE_FOR_RATE} because it would be noise."
        )
        return summary

    hits = sum(1 for _, hit in directional if hit)
    summary["status"] = "reported"
    summary["hit_rate"] = round(hits / len(directional), 4)

    # By uncertainty tier — this is the calibration question that makes the
    # tier mean something: does a "low" reading actually do better?
    by_tier: dict[str, dict] = {}
    for r, hit in directional:
        tier = r.uncertainty_tier or "unknown"
        b = by_tier.setdefault(tier, {"n": 0, "hits": 0})
        b["n"] += 1
        b["hits"] += 1 if hit else 0
    summary["by_uncertainty_tier"] = {
        # Buckets under the floor report their count and withhold the rate,
        # rather than being dropped (which would hide sparse tiers) or shown
        # (which would imply a measurement).
        tier: {
            "n": b["n"],
            "hit_rate": round(b["hits"] / b["n"], 4) if b["n"] >= MIN_SAMPLE_FOR_RATE else None,
        }
        for tier, b in sorted(by_tier.items())
    }
    return summary
