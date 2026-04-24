"""Decision pipeline stage schemas.

Maps to API Contract doc 12, Decision Breakdown endpoints.
"""
from datetime import datetime

from pydantic import BaseModel


class AssetSelection(BaseModel):
    asset_id: str
    ticker: str
    reason: str | None = None


class SelectionRunView(BaseModel):
    id: str
    recommendation_id: str
    included: list[AssetSelection]
    excluded: list[AssetSelection]
    rationale: str | None = None
    created_at: datetime


class AllocationEntry(BaseModel):
    asset_id: str
    ticker: str
    weight: float
    rationale: str | None = None


class AllocationView(BaseModel):
    id: str
    recommendation_id: str
    method: str | None = None
    entries: list[AllocationEntry]
    rationale: str | None = None
    created_at: datetime


class TimingView(BaseModel):
    id: str
    recommendation_id: str
    urgency: str | None = None  # immediate, soon, wait, defer
    horizon_days: int | None = None
    rationale: str | None = None
    created_at: datetime


class RiskAdjustment(BaseModel):
    asset_id: str
    ticker: str
    pre_weight: float
    post_weight: float
    delta: float
    reason: str | None = None


class RiskOverlayView(BaseModel):
    id: str
    recommendation_id: str
    portfolio_risk_score: float | None = None
    adjustments: list[RiskAdjustment]
    constraints_applied: list[str]
    rationale: str | None = None
    created_at: datetime


class DecisionStagesResponse(BaseModel):
    """All pipeline stages for a recommendation."""
    recommendation_id: str
    selection: SelectionRunView | None = None
    allocation: AllocationView | None = None
    timing: TimingView | None = None
    risk_overlay: RiskOverlayView | None = None
