"""Engine and signal schemas for multi-engine comparison.

Maps to design handoff: comparison.jsx ENGINES data structure.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class EngineSignal(BaseModel):
    """Per-engine signal output for a specific asset."""
    engine_key: str
    engine_name: str
    stance: str  # buy, hold, sell, trim
    confidence: float
    weight: float  # engine's portfolio weight contribution
    risk_read: str  # Low, Moderate, Elevated, High
    horizon: str  # 1M, 3M, 6M, 12M
    drivers: list[str] = Field(default_factory=list)
    ignores: list[str] = Field(default_factory=list)
    note: str | None = None
    data_freshness_min: int | None = None


class EngineComparisonResponse(BaseModel):
    """Multi-engine comparison for the current recommendation."""
    recommendation_id: str
    engines: list[EngineSignal]
    synthesis_stance: str
    synthesis_confidence: float
    dispersion: float  # 0-1, how much engines disagree


class DisagreementSummary(BaseModel):
    """Summary of engine disagreement for the decision workspace."""
    recommendation_id: str
    total_engines: int
    agreeing: int
    dissenting: int
    dispersion: float
    dominant_stance: str
    dissenting_engines: list[str]
    summary: str
