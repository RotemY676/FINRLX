"""Finnhub fundamentals provider — Phase 16.0 SHIM (real impl in 16.2).

Why this exists in 16.0:
  - The router can offer "finnhub" as a registered choice from day one,
    so `FUNDAMENTALS_PROVIDER=finnhub` doesn't 500 the moment it's set.
  - The shim returns the stub payload but tags `source="finnhub"` and
    leaves `coverage_note` explaining the activation gap.
  - When the real implementation lands in 16.2 (Finnhub HTTP calls +
    cache + parsing), the only file that changes is this one.

Phase 16.2 implementation outline (kept here as a TODO so the next
session has the contract pinned):

    GET /api/v1/stock/profile2?symbol=NVDA
        -> name, ticker, finnhubIndustry, marketCapitalization,
           shareOutstanding, weburl, sector (inferred)
    GET /api/v1/stock/metric?symbol=NVDA&metric=all
        -> peRatio, forwardPe, priceToBook, priceToSales,
           grossMargin5Y, operatingMargin5Y, netProfitMargin5Y,
           dividendYieldIndicatedAnnual, 52WeekHigh, 52WeekLow,
           revenueTTM, revenueGrowthQuarterlyYoy, epsTTM
    GET /api/v1/stock/peers?symbol=NVDA
        -> list[str]  (peer tickers)
    GET /api/v1/quote?symbol=AAPL  (per peer)
        -> c (current), d (change), dp (percent change)

Rate-limit guard: 60 calls/min on free tier; with the 24h peer cache
and 6h fundamentals cache, this stays well under even with hot use.
"""
from __future__ import annotations

from datetime import UTC, datetime

from app.services.fundamentals.provider import FundamentalsProvider
from app.services.fundamentals.types import (
    FundamentalsResponse,
    PeersResponse,
)


_SHIM_NOTE = (
    "Finnhub provider selected but the live HTTP implementation lands in "
    "Phase 16.2. Endpoint contract is stable. Set FUNDAMENTALS_PROVIDER=stub "
    "to switch back to the explicit stub label."
)


class FinnhubFundamentalsProvider(FundamentalsProvider):
    """Phase 16.0 shim — wire frame, no real calls yet."""

    name: str = "finnhub"
    IS_STUB: bool = False

    def __init__(self, api_key: str) -> None:
        # The key is captured at construction so the router's `if api_key`
        # gate keeps this constructor unreachable when the key is empty.
        # Stored only for the Phase 16.2 HTTP client; not logged.
        self._api_key = api_key

    async def get_fundamentals(self, ticker: str) -> FundamentalsResponse:
        return FundamentalsResponse(
            ticker=ticker.upper(),
            source="finnhub",
            cached_at=datetime.now(UTC).isoformat(),
            coverage_note=_SHIM_NOTE,
        )

    async def get_peers(self, ticker: str) -> PeersResponse:
        return PeersResponse(
            target_ticker=ticker.upper(),
            peers=[],
            source="finnhub",
            cached_at=datetime.now(UTC).isoformat(),
            coverage_note=_SHIM_NOTE,
        )
