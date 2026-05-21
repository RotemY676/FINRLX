"""Phase TPL-2 — recommendation-template API schemas."""
from __future__ import annotations

from pydantic import BaseModel


class TemplateMetricsResponse(BaseModel):
    equity_pct: float
    defensive_pct: float
    expected_annual_return_pct: float
    expected_volatility_pct: float
    expected_max_drawdown_pct: float
    sharpe_estimate: float
    confidence_label: str
    methodology_note: str


class RecommendationTemplateResponse(BaseModel):
    id: str
    key: str
    name: str
    description: str
    badge: str
    risk_bucket: str
    horizon_band: str
    primary_goal: str
    max_drawdown_pct: float
    sector_whitelist: list[str]
    sector_blacklist: list[str]
    exclude_leverage: bool
    base_currency: str
    trading_frequency: str
    region_preference: str
    is_seed: bool
    is_active: bool
    allocation_summary: str | None
    metrics: TemplateMetricsResponse
