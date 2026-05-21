"""Phase TPL-2 / TPL-4 — recommendation-template API schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class TemplateMetricsResponse(BaseModel):
    equity_pct: float
    defensive_pct: float
    expected_annual_return_pct: float
    expected_volatility_pct: float
    expected_max_drawdown_pct: float
    sharpe_estimate: float
    confidence_label: str
    methodology_note: str


class RecommendationTemplateCreate(BaseModel):
    """Phase TPL-4 — admin payload for authoring a new template.

    ``key`` is the slug (URL-addressable). Cannot collide with an
    existing template (DB-level UNIQUE). ``is_seed`` is always False
    here; seeds are loaded via the seed script.
    """

    key: str = Field(..., min_length=1, max_length=60)
    name: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1)
    badge: str = Field(..., min_length=1, max_length=40)
    risk_bucket: str
    horizon_band: str
    primary_goal: str
    max_drawdown_pct: float = Field(..., gt=0, le=100)
    sector_whitelist: list[str] = Field(default_factory=list)
    sector_blacklist: list[str] = Field(default_factory=list)
    exclude_leverage: bool = True
    base_currency: str = "USD"
    trading_frequency: str = "monthly"
    region_preference: str = "global"


class RecommendationTemplateUpdate(BaseModel):
    """Phase TPL-4 — admin partial-update payload.

    All fields optional. ``key`` is immutable (URL identity).
    """

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    badge: str | None = Field(default=None, max_length=40)
    risk_bucket: str | None = None
    horizon_band: str | None = None
    primary_goal: str | None = None
    max_drawdown_pct: float | None = Field(default=None, gt=0, le=100)
    sector_whitelist: list[str] | None = None
    sector_blacklist: list[str] | None = None
    exclude_leverage: bool | None = None
    base_currency: str | None = None
    trading_frequency: str | None = None
    region_preference: str | None = None
    is_active: bool | None = None


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
