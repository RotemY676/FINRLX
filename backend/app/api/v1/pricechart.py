"""Price chart endpoint with deterministic demo data.

GET /api/v1/pricechart?ticker=NVDA — returns time-series + events + confidence band.
"""
import random

from fastapi import APIRouter, Query

from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.schemas.pricechart import ChartEvent, PriceChartData, PricePoint

router = APIRouter()

# Deterministic seed for reproducible chart data
random.seed(42)

# Pre-generate chart data for key tickers
MONTHS = ["Jan", "Feb", "Mar", "Apr"]
DATES = [
    "2026-01-06", "2026-01-13", "2026-01-20", "2026-01-27",
    "2026-02-03", "2026-02-10", "2026-02-17", "2026-02-24",
    "2026-03-03", "2026-03-10", "2026-03-17", "2026-03-24",
    "2026-04-01", "2026-04-07", "2026-04-14", "2026-04-21",
]


def _generate_series(start: float, drift: float, vol: float) -> list[float]:
    """Generate a random-walk price series."""
    rng = random.Random(int(start * 100))
    prices = [start]
    for _ in range(len(DATES) - 1):
        change = drift + rng.gauss(0, vol)
        prices.append(round(prices[-1] * (1 + change), 2))
    return prices


def _make_chart(ticker: str, start: float, drift: float, vol: float,
                bench_start: float, bench_drift: float, events: list[ChartEvent]) -> PriceChartData:
    prices = _generate_series(start, drift, vol)
    bench = _generate_series(bench_start, bench_drift, vol * 0.6)
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
        # Generate a generic chart for unknown tickers
        chart = _make_chart(ticker.upper(), 100, 0.005, 0.02, 100, 0.004, [])
    return ApiResponse(meta=make_meta(), data=chart)
