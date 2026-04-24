"""Recommendation API schemas.

Maps to API Contract doc 12 and Data Model doc 11.
The Recommendation Object is the canonical output of the decision pipeline.
"""
from datetime import datetime

from pydantic import BaseModel, Field


class ConfidenceTriplet(BaseModel):
    """Trust decomposition: model, data, operational confidence."""
    model_confidence: float | None = None
    data_confidence: float | None = None
    operational_confidence: float | None = None


class WeightEntry(BaseModel):
    """Per-asset weight within a recommendation."""
    asset_id: str
    ticker: str
    name: str
    target_weight: float
    previous_weight: float | None = None
    delta: float | None = None
    stance: str | None = None  # overweight, underweight, neutral, exit
    rationale: str | None = None


class RecommendationSummary(BaseModel):
    """Compact recommendation for overview/list views."""
    id: str
    status: str
    confidence: ConfidenceTriplet
    total_positions: int
    top_overweight: str | None = None
    top_underweight: str | None = None
    published_at: datetime | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    data_as_of: datetime | None = None
    rationale_summary: str | None = None
    warning_count: int = 0


class RecommendationDetail(BaseModel):
    """Full recommendation with weights and all metadata."""
    id: str
    status: str
    confidence: ConfidenceTriplet
    weights: list[WeightEntry]
    published_at: datetime | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    data_as_of: datetime | None = None
    rationale_summary: str | None = None
    warnings: list[str] = Field(default_factory=list)
    policy_version_id: str | None = None
    created_at: datetime
