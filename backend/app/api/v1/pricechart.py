"""Price chart endpoint — REAL data only (Operation Credibility, K1).

History note (credibility audit 2026-07-07, Finding B): the previous version
of this file generated hash-seeded synthetic price walks, a fabricated
benchmark, a fictional "confidence band", and invented news events — served
in production one click away from the real dossier price. It is replaced
wholesale by the same provider chain the dossier uses, so every surface
renders the same close for the same ticker+date ("one price truth",
contract-tested in tests/test_k1_one_price_truth.py).

Honesty rules encoded here:
  - No data from the chain -> data: null with nothing drawn. Never a synthetic curve.
  - Benchmark is real SPY, REBASED to the ticker's first close so both lines
    share an axis; the label says "rebased". Benchmark unavailable -> omitted.
  - No confidence band (the old one was fiction).
  - No events (real evidence-linked markers come from the desk feed; this
    endpoint will never invent headlines).
"""
from __future__ import annotations

import logging
import threading
import time

from fastapi import APIRouter, Query

from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.schemas.pricechart import PriceChartData, PricePoint

logger = logging.getLogger(__name__)
router = APIRouter(tags=["pricechart"])

CHART_SESSIONS = 260  # ~1 trading year
HISTORY_DAYS = 420    # calendar days fetched to cover it
_CACHE_TTL_S = 900
_cache: dict[str, tuple[float, PriceChartData | None]] = {}
_lock = threading.Lock()


def _build_chart(ticker: str) -> PriceChartData | None:
    from app.services.single_ticker_analysis import fetch_history

    sym = ticker.upper().strip()
    try:
        bars = fetch_history(sym, HISTORY_DAYS)
    except Exception as exc:  # noqa: BLE001 — provider boundary
        logger.warning("pricechart: no history for %s: %s", sym, exc)
        return None
    if not bars.closes:
        return None
    dates = [d.isoformat() for d in bars.dates[-CHART_SESSIONS:]]
    closes = bars.closes[-CHART_SESSIONS:]

    # Real benchmark (SPY), rebased to the ticker's first close so the two
    # real lines share one axis. Absence is omitted, never simulated.
    bench_by_date: dict[str, float] = {}
    bench_name = "SPY (rebased)"
    try:
        spy = fetch_history("SPY", HISTORY_DAYS)
        spy_map = {d.isoformat(): c for d, c in zip(spy.dates, spy.closes, strict=False)}
        first_spy = next((spy_map[d] for d in dates if d in spy_map), None)
        if first_spy:
            scale = closes[0] / first_spy
            bench_by_date = {
                d: round(spy_map[d] * scale, 4) for d in dates if d in spy_map
            }
    except Exception as exc:  # noqa: BLE001
        logger.info("pricechart: benchmark unavailable: %s", exc)

    points = [
        PricePoint(date=d, price=round(c, 4), benchmark=bench_by_date.get(d))
        for d, c in zip(dates, closes, strict=True)
    ]
    bench_vals = [p.benchmark for p in points if p.benchmark is not None]
    return PriceChartData(
        ticker=sym,
        current_price=round(closes[-1], 4),
        price_return_pct=round((closes[-1] / closes[0] - 1) * 100, 1),
        benchmark_return_pct=(
            round((bench_vals[-1] / bench_vals[0] - 1) * 100, 1)
            if len(bench_vals) >= 2 else None
        ),
        benchmark_name=bench_name,
        points=points,
        events=[],  # real markers live in the desk's evidence-linked feed
    )


@router.get("/pricechart", response_model=ApiResponse[PriceChartData | None])
def get_price_chart(ticker: str = Query("NVDA")):
    sym = ticker.upper().strip()
    now = time.time()
    with _lock:
        hit = _cache.get(sym)
        if hit and now - hit[0] < _CACHE_TTL_S:
            return ApiResponse(meta=make_meta(), data=hit[1])
    chart = _build_chart(sym)
    with _lock:
        _cache[sym] = (now, chart)
    return ApiResponse(meta=make_meta(), data=chart)
