"""Scenario simulation schemas.

Maps to design handoff: scenario.jsx ScenarioCard controls + delta preview.
"""
from pydantic import BaseModel, Field


class ScenarioParams(BaseModel):
    """Input parameters for scenario simulation."""
    horizon_days: int = Field(42, ge=7, le=180)
    rate_shock_bps: int = Field(0, ge=-200, le=200)
    correlation: float = Field(0.55, ge=0.0, le=1.0)
    earnings_revision_weight: float = Field(0.60, ge=0.0, le=1.0)
    momentum_engine_on: bool = True
    flow_engine_on: bool = False
    policy_constraints_on: bool = True


class ScenarioDelta(BaseModel):
    """Single metric delta between baseline and modified scenario."""
    metric: str
    baseline: str
    modified: str
    direction: str  # pos, neg, neutral


class ScenarioResult(BaseModel):
    """Result of a scenario simulation run."""
    is_modified: bool
    deltas: list[ScenarioDelta] = Field(default_factory=list)
    weight_impact: float  # e.g. -0.6 means weight drops 0.6%
    confidence_impact: float  # e.g. -0.05
    expected_return_impact: float  # e.g. -1.5%
    warnings: list[str] = Field(default_factory=list)
