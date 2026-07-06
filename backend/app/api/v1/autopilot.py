"""PROGRAM LEAP S2 — Autopilot dossier endpoint.

GET /api/v1/autopilot/dossier?ticker=NVDA

Returns the full 360-degree research dossier as JSON (schema E.4).
Mirrors /analysis/single-ticker conventions: strict server-side ticker
validation (D40), thread-offloaded pipeline, clean error mapping.
Dossiers are research analysis, not recommendations (D30).
"""
from __future__ import annotations

import asyncio
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.autopilot import HISTORY_DAYS_DEFAULT, build_dossier
from app.services.autopilot_store import (
    COMPARISON_MAX_TICKERS,
    build_comparison,
    persist_dossier,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/autopilot/dossier",
    summary="360-degree automatic research dossier for one ticker",
    description=(
        "Zero-config pipeline: ingest prices, enrich with news+sentiment, "
        "compute the technical vocabulary, run the automatic model "
        "tournament (walk-forward validated, overfitting-penalized), and "
        "return the assembled dossier with per-stage timings, evidence, "
        "and disclaimers."
    ),
)
async def autopilot_dossier(
    ticker: str = Query(..., min_length=1, max_length=10,
                        description="Stock ticker symbol (e.g. NVDA, BRK.B)"),
    db: AsyncSession = Depends(get_db),
):
    t0 = time.time()
    try:
        dossier = await asyncio.to_thread(
            build_dossier, ticker, history_days=HISTORY_DAYS_DEFAULT
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:  # noqa: BLE001 — boundary; clean 500
        logger.exception("autopilot dossier failed for %s", ticker)
        raise HTTPException(status_code=500, detail=f"Autopilot failed: {e}")
    try:
        await persist_dossier(db, dossier)
        await db.commit()
    except Exception:  # noqa: BLE001 — persistence must never fail the read path
        logger.exception("dossier persistence failed for %s (serving anyway)", ticker)
        await db.rollback()

    elapsed_ms = int((time.time() - t0) * 1000)
    logger.info("autopilot dossier %s: %d ms (cache=%s)",
                dossier["ticker"], elapsed_ms, dossier.get("served_from_cache"))
    return {"meta": {"duration_ms": elapsed_ms}, "data": dossier}


@router.get(
    "/autopilot/compare",
    summary="Side-by-side comparison of 2-4 tickers on shared dossier dimensions",
    description=(
        "Serves each ticker's dossier (persisted when current, freshly built "
        "otherwise) and assembles the shared comparison dimensions plus "
        "measured divergence highlights. Research analysis, not advice."
    ),
)
async def autopilot_compare(
    tickers: str = Query(..., description="Comma-separated tickers, 2-4, e.g. NVDA,AMD"),
    db: AsyncSession = Depends(get_db),
):
    raw = [t for t in (p.strip() for p in tickers.split(",")) if t]
    if not 2 <= len(raw) <= COMPARISON_MAX_TICKERS:
        raise HTTPException(
            status_code=400,
            detail=f"Provide 2-{COMPARISON_MAX_TICKERS} comma-separated tickers.",
        )
    try:
        result = await build_comparison(db, raw)
        await db.commit()
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return {"data": result}
