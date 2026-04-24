"""ML model registry schemas."""
from datetime import date, datetime
from pydantic import BaseModel, Field


class ModelDefinitionResponse(BaseModel):
    id: str
    key: str
    name: str
    category: str
    description: str | None = None
    model_type: str
    target: str
    feature_keys: list[str] | None = None
    prediction_horizon_days: int
    version: str
    status: str
    is_shadow: bool


class ModelRunResponse(BaseModel):
    id: str
    model_key: str
    run_type: str
    status: str
    metrics: dict | None = None
    warnings: list[str] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ModelPredictionResponse(BaseModel):
    asset_id: str
    ticker: str
    as_of: date
    prediction_value: float | None = None
    prediction_score: float | None = None
    confidence: float | None = None
    quality: str
    drivers: list[str] | None = None


class ModelTrainRequest(BaseModel):
    model_key: str = "ml_return_forecaster"
    train_start_date: str | None = None
    train_end_date: str | None = None


class ModelPredictRequest(BaseModel):
    model_key: str = "ml_return_forecaster"
    feature_set_id: str | None = None


class ModelStatusResponse(BaseModel):
    total_definitions: int = 0
    active_definitions: int = 0
    total_runs: int = 0
    total_predictions: int = 0
    latest_run_id: str | None = None
    latest_run_status: str | None = None
    latest_validation_status: str | None = None
    directional_accuracy: float | None = None
    validation_sample_count: int | None = None
    promotion_readiness: str | None = None
