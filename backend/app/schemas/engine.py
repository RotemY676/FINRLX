"""Engine and signal schemas.

Maps to Doc 11 Domain 4 and Doc 12 engine endpoints.
Preserves backward-compatible response shapes for existing frontend consumers.
"""
from datetime import datetime
from pydantic import BaseModel, Field


# ── Engine definition ─────────────────────────────────────────────────

class EngineDefinitionResponse(BaseModel):
    id: str
    key: str
    name: str
    category: str
    description: str | None = None
    version: str
    required_feature_keys: list[str] | None = None
    output_kind: str
    is_active: bool


# ── Signal output (per-asset per-engine) ──────────────────────────────

class EngineSignal(BaseModel):
    """Per-engine signal output — backward compatible with frontend."""
    engine_key: str
    engine_name: str
    stance: str  # buy, hold, sell, trim
    confidence: float
    weight: float  # engine portfolio weight contribution
    risk_read: str  # Low, Moderate, Elevated, High
    horizon: str  # 1M, 3M, 6M
    drivers: list[str] = Field(default_factory=list)
    ignores: list[str] = Field(default_factory=list)
    note: str | None = None
    data_freshness_min: int | None = None


class EngineSignalDetail(BaseModel):
    """Rich per-asset signal with lineage."""
    engine_key: str
    engine_name: str
    ticker: str
    asset_id: str
    stance: str
    score: float
    confidence: float
    risk_level: str
    drivers: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    source_feature_set_id: str | None = None
    feature_quality_summary: str | None = None
    created_at: datetime | None = None


# ── Comparison / disagreement (backward compatible) ───────────────────

class EngineComparisonResponse(BaseModel):
    recommendation_id: str
    engines: list[EngineSignal]
    synthesis_stance: str
    synthesis_confidence: float
    dispersion: float


class DisagreementSummary(BaseModel):
    recommendation_id: str
    total_engines: int
    agreeing: int
    dissenting: int
    dispersion: float
    dominant_stance: str
    dissenting_engines: list[str]
    summary: str


# ── Engine run request/result ─────────────────────────────────────────

class EngineRunRequest(BaseModel):
    feature_set_id: str | None = None
    engine_keys: list[str] | None = None


class EngineRunResult(BaseModel):
    run_id: str
    engine_key: str
    status: str
    signal_count: int
    message: str


class EngineRunResponse(BaseModel):
    results: list[EngineRunResult]
    total_engines: int
    successful: int
    failed: int
    feature_set_id: str | None = None


class EngineRunDetailResponse(BaseModel):
    run_id: str
    engine_name: str
    engine_version: str | None = None
    feature_set_id: str | None = None
    status: str
    run_started_at: datetime | None = None
    run_completed_at: datetime | None = None
    data_as_of: datetime | None = None
    signal_count: int = 0


class EngineStatusResponse(BaseModel):
    total_definitions: int
    active_definitions: int
    latest_run_id: str | None = None
    latest_run_at: datetime | None = None
    latest_run_status: str | None = None
    latest_feature_set_id: str | None = None
