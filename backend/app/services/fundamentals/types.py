"""Fundamentals + Peers response schemas.

Every field that depends on a real third-party data source is `Optional`
so the stub provider can return a structurally-complete envelope without
inventing numbers.  Frontend renders `null`/`None` as an honest "—" or
hides the tile entirely (per finrlx-fintech-dashboard-patterns: a tile
without a value is honest, a tile with an invented value is not).
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class FundamentalsResponse(BaseModel):
    """Structured fundamentals payload for /research/fundamentals/{ticker}.

    Every numeric is Optional so partial coverage from the provider does
    not require the frontend to invent. `source` and `as_of` are the
    provenance contract every fundamentals tile must surface.
    """

    ticker: str
    company_name: str | None = None
    sector: str | None = None
    industry: str | None = None
    description: str | None = None

    # Valuation
    market_cap_usd: float | None = None
    pe_ratio_ttm: float | None = None
    forward_pe: float | None = None
    price_to_book: float | None = None
    price_to_sales_ttm: float | None = None
    ev_to_ebitda: float | None = None

    # Profitability (as 0..1 ratios)
    gross_margin_ttm: float | None = None
    operating_margin_ttm: float | None = None
    net_margin_ttm: float | None = None

    # Growth / scale
    revenue_ttm_usd: float | None = None
    revenue_growth_yoy: float | None = None
    eps_ttm: float | None = None

    # Income
    dividend_yield: float | None = None

    # Range
    week_52_high: float | None = Field(default=None, alias="52w_high")
    week_52_low: float | None = Field(default=None, alias="52w_low")

    # Provenance — surfaced on every tile
    as_of: str | None = None  # ISO date the provider says the metrics are as-of
    source: str = "stub"  # provider name ("finnhub", "fmp", "stub")
    cached_at: str | None = None  # ISO timestamp WE fetched / cached
    coverage_note: str | None = None  # honest "data unavailable for this ticker" string

    model_config = {"populate_by_name": True}


class PeerEntry(BaseModel):
    ticker: str
    name: str | None = None
    sector: str | None = None
    industry: str | None = None
    market_cap_usd: float | None = None
    last_close_usd: float | None = None
    change_pct_1d: float | None = None  # as 0..1 ratio, e.g. 0.0123 = +1.23%
    change_pct_ytd: float | None = None


class PeersResponse(BaseModel):
    target_ticker: str
    target_sector: str | None = None
    target_industry: str | None = None
    peers: list[PeerEntry] = Field(default_factory=list)

    as_of: str | None = None
    source: str = "stub"
    cached_at: str | None = None
    coverage_note: str | None = None
