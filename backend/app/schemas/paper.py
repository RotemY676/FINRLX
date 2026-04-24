"""Paper portfolio schemas.

Maps to Data Model doc 11, Domain 7 and API Contract doc 12.
"""
from datetime import datetime

from pydantic import BaseModel, Field


class PaperHolding(BaseModel):
    asset_id: str
    ticker: str
    name: str
    target_weight: float
    current_weight: float
    drift: float  # current - target


class PaperEvent(BaseModel):
    timestamp: datetime
    event_type: str  # rebalance, drift_alert, creation
    description: str


class PaperPortfolioDetail(BaseModel):
    id: str
    name: str
    is_active: bool
    cash_weight: float
    invested_weight: float
    total_rebalances: int
    last_rebalance_at: datetime | None = None
    holdings: list[PaperHolding]
    events: list[PaperEvent] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime
