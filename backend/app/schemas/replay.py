"""Replay schemas.

Maps to Data Model doc 11, Domain 7 and API Contract doc 12.
"""
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.recommendation import ConfidenceTriplet, WeightEntry


class ReplayStageSnapshot(BaseModel):
    stage: str
    snapshot_data: dict
    captured_at: datetime


class ReplayDetail(BaseModel):
    """Full replay of a historical recommendation state."""
    id: str
    recommendation_id: str
    captured_at: datetime
    # Recommendation state at capture
    status: str
    confidence: ConfidenceTriplet
    weights: list[WeightEntry]
    rationale_summary: str | None = None
    warnings: list[str] = Field(default_factory=list)
    data_as_of: datetime | None = None
    # Stage snapshots
    stages: list[ReplayStageSnapshot] = Field(default_factory=list)


class ReplayListItem(BaseModel):
    id: str
    recommendation_id: str
    captured_at: datetime
    status: str
    total_positions: int
    model_confidence: float | None = None


class ReplayListResponse(BaseModel):
    items: list[ReplayListItem]
    total: int
