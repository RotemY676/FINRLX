"""Single-ticker deep-analysis endpoint.

Runs the FINRLX feature -> engine ensemble -> 7-strategy walk-forward
backtest pipeline for one ticker and returns a self-contained HTML
report. Frontend wizard at /analyze embeds the response in an iframe.

The pipeline is CPU/IO bound (~5-10s end-to-end). We run it in a
threadpool via asyncio.to_thread so other requests aren't blocked
during the analysis.
"""
from __future__ import annotations

import asyncio
import logging
import re
import time

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.services.single_ticker_analysis import run_full_analysis

logger = logging.getLogger(__name__)

router = APIRouter()

# Tickers are uppercase letters/digits with optional dot or hyphen
# (e.g. BRK.B, BF-A). Max 10 chars covers all real instruments.
_TICKER_PATTERN = re.compile(r"^[A-Z0-9.\-]{1,10}$")


@router.get(
    "/analysis/single-ticker",
    response_class=HTMLResponse,
    summary="Single-ticker multi-strategy HTML report",
    description=(
        "Fetches OHLCV + ticker news, runs the FINRLX engine ensemble, "
        "executes a 7-strategy walk-forward backtest, and returns a "
        "self-contained HTML document. Takes ~5-10 seconds."
    ),
)
async def single_ticker_analysis(
    ticker: str = Query(
        ...,
        min_length=1,
        max_length=10,
        description="Stock ticker symbol (e.g. UMC, NVDA, BRK.B)",
    ),
    history_days: int = Query(
        400,
        ge=120,
        le=2000,
        description="Days of OHLCV history to fetch (default 400)",
    ),
    backtest_days: int = Query(
        365,
        ge=60,
        le=1500,
        description="Days the walk-forward backtest covers (default 365)",
    ),
) -> HTMLResponse:
    sym = ticker.upper().strip()
    if not _TICKER_PATTERN.match(sym):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ticker symbol: {ticker!r}. Use 1-10 uppercase letters/digits/.-",
        )

    t0 = time.time()
    try:
        result = await asyncio.to_thread(
            run_full_analysis,
            sym,
            history_days=history_days,
            backtest_days=backtest_days,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # yfinance returned nothing — symbol probably doesn't exist or is delisted.
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:  # noqa: BLE001 — boundary; convert to a clean 500
        logger.exception("single-ticker analysis failed for %s", sym)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    elapsed_ms = int((time.time() - t0) * 1000)
    logger.info("single-ticker analysis %s: %d ms", sym, elapsed_ms)
    response = HTMLResponse(content=result.html, status_code=200)
    response.headers["X-Analysis-Duration-Ms"] = str(elapsed_ms)
    response.headers["X-Analysis-Ticker"] = sym
    # Caches discouraged: each run pulls live yfinance data, so identical
    # requests within a minute may still differ if a new bar prints.
    response.headers["Cache-Control"] = "no-store"
    return response
