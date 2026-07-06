"""LEAP F1.6 — price-freshness API for Pro surfaces.

GET /api/v1/prices/freshness            -> full watchdog report
GET /api/v1/prices/freshness?ticker=X   -> one ticker's status (404 if no bars)

Read-only view over app.services.price_freshness (D6 thresholds, F2
calendar-aware). Frontend badges bind status -> existing token treatments.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.price_freshness import evaluate_price_freshness

router = APIRouter()


@router.get("/prices/freshness", summary="Equity price freshness (D6 tiers)")
async def price_freshness(
    ticker: str | None = Query(default=None, max_length=20),
    db: AsyncSession = Depends(get_db),
):
    report = await evaluate_price_freshness(db)
    payload = {
        "evaluated_at": report.evaluated_at.isoformat(),
        "expected_latest_session": report.expected_latest_session_iso,
        "tickers": [t.__dict__ for t in report.tickers],
        "counts": {
            "fresh": len(report.tickers) - len(report.stale) - len(report.degraded),
            "stale": len(report.stale),
            "degraded": len(report.degraded),
        },
    }
    if ticker is None:
        return {"data": payload}
    sym = ticker.upper().strip()
    match = next((t for t in report.tickers if t.ticker == sym), None)
    if match is None:
        raise HTTPException(status_code=404, detail=f"No price bars for {sym}")
    return {"data": {**match.__dict__, "expected_latest_session": report.expected_latest_session_iso}}
