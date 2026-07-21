"""Canonical DecisionPacket read-only endpoint (US-DPK-03, P1 / EP-1).

Projects an existing ``Recommendation`` into per-ticker ``DecisionPacket``
objects and exposes each packet's explicit truth-gate outcome
(blocked / research_only / ready_for_review).

Gated behind the ``decision_packet_v1`` feature flag (default OFF). When the
flag is disabled the surface returns 404, so legacy consumers see no behavior
change. The projection is strictly read-only and never fabricates evidence:
packets built from the current pipeline are honestly blocked or research-only
because calibrated forecasts, reproducible backtests, prospective validation
and risk frames do not yet exist upstream. Nothing here authorizes broker
execution or promises future returns.
"""
from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import get_optional_user
from app.api.deps import make_meta
from app.core.config import settings
from app.core.database import get_db
from app.models.auth import User
from app.models.ingestion import MarketBar
from app.models.recommendation import Recommendation, RecommendationWeight
from app.models.reference import Asset
from app.schemas.common import ApiResponse
from app.schemas.decision_packet import DecisionPacketBundle, DecisionTruthPolicy
from app.services.decision_packet_adapter import build_recommendation_packets
from app.services.price_freshness import evaluate_price_freshness

router = APIRouter()

_FLAG_OFF = HTTPException(status_code=404, detail="Decision packet surface is not enabled")
_NOT_FOUND = HTTPException(status_code=404, detail="Recommendation not found")


async def _latest_bar_sources(db: AsyncSession, tickers: set[str]) -> dict[str, str | None]:
    """Return the source of the latest unflagged bar for each requested ticker."""
    if not tickers:
        return {}
    latest = (
        select(MarketBar.ticker, func.max(MarketBar.bar_date).label("md"))
        .where(MarketBar.quality_flag.is_(None))
        .where(MarketBar.ticker.in_(tickers))
        .group_by(MarketBar.ticker)
        .subquery()
    )
    rows = (
        await db.execute(
            select(MarketBar.ticker, MarketBar.source).join(
                latest,
                and_(
                    MarketBar.ticker == latest.c.ticker,
                    MarketBar.bar_date == latest.c.md,
                ),
            )
        )
    ).all()
    return {ticker: source for ticker, source in rows}


@router.get(
    "/recommendations/{recommendation_id}/decision-packets",
    response_model=ApiResponse[DecisionPacketBundle],
)
async def get_decision_packets(
    recommendation_id: str,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    # Fail closed: the surface does not exist unless the flag is on.
    if not settings.feature_decision_packet_v1:
        raise _FLAG_OFF

    rec = (
        await db.execute(select(Recommendation).where(Recommendation.id == recommendation_id))
    ).scalar_one_or_none()
    if rec is None:
        raise _NOT_FOUND

    # Resource authorization: an owned recommendation is only visible to its
    # owner. Respond 404 (not 403) so ownership is not disclosed to others.
    if rec.user_id is not None and (user is None or user.id != rec.user_id):
        raise _NOT_FOUND

    weights = list(
        (
            await db.execute(
                select(RecommendationWeight).where(
                    RecommendationWeight.recommendation_id == rec.id
                )
            )
        )
        .scalars()
        .all()
    )

    asset_ids = {w.asset_id for w in weights}
    ticker_by_asset: dict[str, str] = {}
    if asset_ids:
        asset_rows = (
            await db.execute(select(Asset.id, Asset.ticker).where(Asset.id.in_(asset_ids)))
        ).all()
        ticker_by_asset = {aid: ticker for aid, ticker in asset_rows}

    now = datetime.now(UTC)
    report = await evaluate_price_freshness(db, now=now)
    freshness_by_ticker = {tf.ticker: tf for tf in report.tickers}
    expected_latest_session: date = date.fromisoformat(report.expected_latest_session_iso)

    tickers = {ticker_by_asset[a] for a in asset_ids if a in ticker_by_asset}
    source_by_ticker = await _latest_bar_sources(db, tickers)

    packets = build_recommendation_packets(
        rec=rec,
        weights=weights,
        ticker_by_asset=ticker_by_asset,
        freshness_by_ticker=freshness_by_ticker,
        source_by_ticker=source_by_ticker,
        expected_latest_session=expected_latest_session,
        now=now,
    )

    outcomes = Counter(p.gate.outcome.value for p in packets)
    bundle = DecisionPacketBundle(
        recommendation_id=rec.id,
        policy_version=DecisionTruthPolicy().version,
        count=len(packets),
        outcomes=dict(outcomes),
        packets=packets,
    )
    return ApiResponse(meta=make_meta(), data=bundle)
