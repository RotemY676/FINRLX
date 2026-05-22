"""Fundamentals + Peers response schemas.

Every field that depends on a real third-party data source is `Optional`
so the stub provider can return a structurally-complete envelope without
inventing numbers.  Frontend renders `null`/`None` as an honest "—" or
hides the tile entirely (per finrlx-fintech-dashboard-patterns: a tile
without a value is honest, a tile with an invented value is not).
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class FundamentalsResponse(BaseModel):
    """Structured fundamentals payload for /research/fundamentals/{ticker}.

    Every numeric is Optional so partial coverage from the provider does
    not require the frontend to invent. `source` and `as_of` are the
    provenance contract every fundamentals tile must surface.
    """

    ticker: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None

    # Valuation
    market_cap_usd: Optional[float] = None
    pe_ratio_ttm: Optional[float] = None
    forward_pe: Optional[float] = None
    price_to_book: Optional[float] = None
    price_to_sales_ttm: Optional[float] = None
    ev_to_ebitda: Optional[float] = None

    # Profitability (as 0..1 ratios)
    gross_margin_ttm: Optional[float] = None
    operating_margin_ttm: Optional[float] = None
    net_margin_ttm: Optional[float] = None

    # Growth / scale
    revenue_ttm_usd: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None
    eps_ttm: Optional[float] = None

    # Income
    dividend_yield: Optional[float] = None

    # Range
    week_52_high: Optional[float] = Field(default=None, alias="52w_high")
    week_52_low: Optional[float] = Field(default=None, alias="52w_low")

    # Provenance — surfaced on every tile
    as_of: Optional[str] = None  # ISO date the provider says the metrics are as-of
    source: str = "stub"  # provider name ("finnhub", "fmp", "stub")
    cached_at: Optional[str] = None  # ISO timestamp WE fetched / cached
    coverage_note: Optional[str] = None  # honest "data unavailable for this ticker" string

    model_config = {"populate_by_name": True}


class PeerEntry(BaseModel):
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap_usd: Optional[float] = None
    last_close_usd: Optional[float] = None
    change_pct_1d: Optional[float] = None  # as 0..1 ratio, e.g. 0.0123 = +1.23%
    change_pct_ytd: Optional[float] = None


class PeersResponse(BaseModel):
    target_ticker: str
    target_sector: Optional[str] = None
    target_industry: Optional[str] = None
    peers: list[PeerEntry] = Field(default_factory=list)

    as_of: Optional[str] = None
    source: str = "stub"
    cached_at: Optional[str] = None
    coverage_note: Optional[str] = None
