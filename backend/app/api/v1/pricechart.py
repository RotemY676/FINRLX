"""Price chart endpoint with deterministic demo data.

GET /api/v1/pricechart?ticker=NVDA — returns time-series + events + confidence band.
"""
import hashlib
import random

from fastapi import APIRouter, Query

from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.schemas.pricechart import ChartEvent, PriceChartData, PricePoint

router = APIRouter()

# Pre-generate chart data for key tickers
MONTHS = ["Jan", "Feb", "Mar", "Apr"]
DATES = [
    "2026-01-06", "2026-01-13", "2026-01-20", "2026-01-27",
    "2026-02-03", "2026-02-10", "2026-02-17", "2026-02-24",
    "2026-03-03", "2026-03-10", "2026-03-17", "2026-03-24",
    "2026-04-01", "2026-04-07", "2026-04-14", "2026-04-21",
]


def _ticker_seed(ticker: str, salt: str = "") -> int:
    """Deterministic per-ticker seed.

    Previous version seeded only on `int(start * 100)` which collided across
    every unknown ticker (start=100 → seed=10000) and produced the IDENTICAL
    price series for TXN, AMD, INTC, … — visible on /research/<ticker>.
    Hashing the ticker (plus an optional salt to decorrelate the price and
    benchmark series) gives a stable per-ticker seed.
    """
    h = hashlib.sha256(f"{ticker.upper()}|{salt}".encode()).hexdigest()
    # 32 bits is enough seed entropy and fits in Python ints comfortably.
    return int(h[:8], 16)


def _generate_series(seed: int, start: float, drift: float, vol: float) -> list[float]:
    """Generate a random-walk price series. The seed must vary per ticker
    so different tickers produce different curves."""
    rng = random.Random(seed)
    prices = [start]
    for _ in range(len(DATES) - 1):
        change = drift + rng.gauss(0, vol)
        prices.append(round(prices[-1] * (1 + change), 2))
    return prices


def _make_chart(ticker: str, start: float, drift: float, vol: float,
                bench_start: float, bench_drift: float, events: list[ChartEvent]) -> PriceChartData:
    # Decorrelate the price line from the benchmark line — without the salt,
    # the benchmark series would inherit the same per-ticker seed and the two
    # lines would track each other suspiciously closely.
    price_seed = _ticker_seed(ticker)
    bench_seed = _ticker_seed(ticker, salt="benchmark")
    prices = _generate_series(price_seed, start, drift, vol)
    bench = _generate_series(bench_seed, bench_start, bench_drift, vol * 0.6)
    band_width = vol * start * 3

    points = []
    for i, date in enumerate(DATES):
        points.append(PricePoint(
            date=date, price=prices[i],
            benchmark=bench[i],
            band_upper=round(prices[i] + band_width, 2),
            band_lower=round(prices[i] - band_width, 2),
        ))

    return PriceChartData(
        ticker=ticker,
        current_price=prices[-1],
        price_return_pct=round((prices[-1] / prices[0] - 1) * 100, 1),
        benchmark_return_pct=round((bench[-1] / bench[0] - 1) * 100, 1),
        benchmark_name="S&P 500",
        points=points,
        events=events,
    )


def _synthetic_chart_for_unknown(ticker: str) -> PriceChartData:
    """Per-ticker synthetic chart for symbols outside the curated CHARTS map.

    start / drift / vol are derived deterministically from the ticker so each
    symbol produces its own distinct (but stable across requests) curve.
    Ranges chosen to look plausible for US equities:
      start: $40–$340
      drift: -0.4% to +1.5% per weekly bar
      vol:   1.0% to 4.0% per weekly bar
    """
    h = hashlib.sha256(ticker.upper().encode()).digest()
    start = 40 + (h[0] / 255) * 300        # 40–340
    drift = -0.004 + (h[1] / 255) * 0.019  # -0.4% to +1.5%
    vol = 0.010 + (h[2] / 255) * 0.030     # 1.0% to 4.0%
    return _make_chart(ticker.upper(), round(start, 2), round(drift, 4),
                       round(vol, 4), 100, 0.005, [])


CHARTS: dict[str, PriceChartData] = {
    "NVDA": _make_chart("NVDA", 920, 0.012, 0.035, 100, 0.005, [
        ChartEvent(date="2026-01-27", label="Q4 earnings · beat +8%", kind="pos"),
        ChartEvent(date="2026-02-24", label="Sector downgrade", kind="neg"),
        ChartEvent(date="2026-03-24", label="Guidance raise", kind="pos"),
    ]),
    "AAPL": _make_chart("AAPL", 195, 0.006, 0.022, 100, 0.005, [
        ChartEvent(date="2026-02-10", label="Services beat", kind="pos"),
        ChartEvent(date="2026-03-17", label="Buyback announced", kind="pos"),
    ]),
    "MSFT": _make_chart("MSFT", 420, 0.008, 0.025, 100, 0.005, [
        ChartEvent(date="2026-01-20", label="Azure growth +31%", kind="pos"),
    ]),
}


@router.get("/pricechart", response_model=ApiResponse[PriceChartData | None])
async def get_price_chart(ticker: str = Query("NVDA")):
    chart = CHARTS.get(ticker.upper())
    if not chart:
        chart = _synthetic_chart_for_unknown(ticker)
    return ApiResponse(meta=make_meta(), data=chart)
