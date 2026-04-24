"""Decision pipeline schemas.

Maps to Doc 10 Section 8 (Canonical Production Flow) and Doc 12.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class PipelineRunRequest(BaseModel):
    universe_id: str | None = None
    signal_run_ids: list[str] | None = None  # None = use latest registered signals
    feature_set_id: str | None = None  # None = auto-resolve best feature set


class PipelineStageResult(BaseModel):
    stage: str
    status: str  # completed, partial, failed
    record_id: str | None = None
    message: str


class PipelineRunResult(BaseModel):
    recommendation_id: str | None = None
    status: str  # completed, partial, failed
    stages: list[PipelineStageResult]
    warnings: list[str] = Field(default_factory=list)
    feature_set_id: str | None = None
    signal_run_ids: list[str] | None = None
    message: str


class PipelineStatusResponse(BaseModel):
    latest_recommendation_id: str | None = None
    latest_status: str | None = None
    latest_created_at: datetime | None = None
    total_pipeline_recommendations: int = 0
    total_published: int = 0
