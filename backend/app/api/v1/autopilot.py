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

from fastapi import APIRouter, HTTPException, Query

from app.services.autopilot import HISTORY_DAYS_DEFAULT, build_dossier

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

    elapsed_ms = int((time.time() - t0) * 1000)
    logger.info("autopilot dossier %s: %d ms (cache=%s)",
                dossier["ticker"], elapsed_ms, dossier.get("served_from_cache"))
    return {"meta": {"duration_ms": elapsed_ms}, "data": dossier}
