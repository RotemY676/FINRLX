"""Feature layer schemas.

Maps to Doc 11 Domain 3 and Doc 12 feature endpoints.
"""
from datetime import date, datetime
from pydantic import BaseModel, Field


class FeatureDefinitionResponse(BaseModel):
    id: str
    key: str
    name: str
    category: str
    description: str | None = None
    version: str
    lookback_days: int
    input_kind: str
    output_type: str
    is_active: bool


class FeatureValueResponse(BaseModel):
    asset_id: str
    ticker: str
    feature_key: str
    value: float | None = None
    unit: str | None = None
    window_days: int | None = None
    quality: str


class FeatureSetResponse(BaseModel):
    id: str
    universe_id: str | None = None
    as_of: date
    status: str
    feature_version: str
    asset_count: int
    feature_count: int
    completeness_score: float
    freshness_status: str
    warnings: list[str] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    values: list[FeatureValueResponse] | None = None  # populated on detail view


class FeatureComputeRequest(BaseModel):
    universe_id: str | None = None
    as_of: date | None = None


class FeatureComputeResult(BaseModel):
    feature_set_id: str
    status: str
    asset_count: int
    feature_count: int
    completeness_score: float
    warnings: list[str]
    message: str


class FeatureStatusResponse(BaseModel):
    latest_feature_set_id: str | None = None
    latest_as_of: date | None = None
    latest_status: str | None = None
    completeness_score: float | None = None
    freshness_status: str | None = None
    total_definitions: int = 0
    active_definitions: int = 0
