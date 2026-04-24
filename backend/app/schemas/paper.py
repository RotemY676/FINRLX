"""Paper portfolio schemas with provenance.

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
    drift: float


class PaperEvent(BaseModel):
    timestamp: datetime | str
    event_type: str
    description: str


class PaperPortfolioDetail(BaseModel):
    id: str
    name: str
    is_active: bool
    source_type: str = "unknown"  # recommendation_paper, seed_demo, test_paper, unknown
    is_demo: bool = True
    lineage_available: bool = False
    source_recommendation_id: str | None = None
    portfolio_value: float = 100000.0
    cash_weight: float
    invested_weight: float
    total_rebalances: int
    last_rebalance_at: datetime | None = None
    holdings: list[PaperHolding]
    events: list[PaperEvent] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime


class PaperDriftResponse(BaseModel):
    portfolio_id: str
    total_value: float
    cash_weight: float
    drifted_positions: list[dict]
    drift_count: int
    max_drift: float


class PaperCreateRequest(BaseModel):
    starting_value: float = 100000.0
    allow_unpublished: bool = False
