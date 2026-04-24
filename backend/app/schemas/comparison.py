"""Comparison schemas.

Supports side-by-side comparison of recommendation vs benchmark.
"""
from pydantic import BaseModel, Field

from app.schemas.recommendation import ConfidenceTriplet, WeightEntry


class ComparisonWeightRow(BaseModel):
    """One row in a side-by-side weight comparison."""
    asset_id: str
    ticker: str
    name: str
    recommendation_weight: float
    benchmark_weight: float
    delta: float
    recommendation_stance: str | None = None


class ComparisonResponse(BaseModel):
    """Side-by-side recommendation vs benchmark comparison."""
    recommendation_id: str
    benchmark_name: str
    recommendation_confidence: ConfidenceTriplet
    weights: list[ComparisonWeightRow]
    recommendation_warning_count: int = 0
    recommendation_rationale: str | None = None
    total_active_weight: float  # sum of abs(delta)
    concentration_top3_rec: float
    concentration_top3_bench: float
