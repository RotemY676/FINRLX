"""ML Ops observability schemas.

Phase 6D: response models for ML ops summary, health, shadow status, etc.
"""
from pydantic import BaseModel


class MLOpsWarning(BaseModel):
    level: str  # info, warning
    message: str


class ModelHealthResponse(BaseModel):
    model_key: str
    model_name: str | None = None
    status: str = "unknown"
    is_shadow: bool = True
    model_type: str | None = None
    latest_prediction_run_id: str | None = None
    latest_prediction_status: str | None = None
    prediction_count: int = 0


class ShadowStatusResponse(BaseModel):
    model_key: str
    is_shadow: bool = True
    still_shadow: bool = True
    live_pipeline_influence: bool = False
    promotion_review_recommendation: str | None = None
    promotion_review_decision: str | None = None


class ValidationSummaryResponse(BaseModel):
    model_key: str
    latest_validation_report_id: str | None = None
    validation_status: str | None = None
    validation_sample_count: int | None = None
    directional_accuracy: float | None = None
    calibration_error: float | None = None
    promotion_readiness: str | None = None
    warnings: list[str] | None = None


class PromotionSummaryResponse(BaseModel):
    model_key: str
    latest_promotion_review_id: str | None = None
    promotion_review_recommendation: str | None = None
    promotion_review_decision: str | None = None
    baseline_total_return: float | None = None
    shadow_total_return: float | None = None
    total_return_delta: float | None = None
    max_drawdown_delta: float | None = None
    sharpe_delta: float | None = None
    warnings: list[str] | None = None


class MLOpsSummaryResponse(BaseModel):
    model_key: str
    model_name: str | None = None
    status: str = "unknown"
    is_shadow: bool = True
    latest_prediction_run_id: str | None = None
    latest_prediction_status: str | None = None
    prediction_count: int = 0
    latest_validation_report_id: str | None = None
    validation_status: str | None = None
    validation_sample_count: int | None = None
    directional_accuracy: float | None = None
    calibration_error: float | None = None
    promotion_readiness: str | None = None
    latest_promotion_review_id: str | None = None
    promotion_review_recommendation: str | None = None
    promotion_review_decision: str | None = None
    baseline_total_return: float | None = None
    shadow_total_return: float | None = None
    total_return_delta: float | None = None
    max_drawdown_delta: float | None = None
    sharpe_delta: float | None = None
    still_shadow: bool = True
    live_pipeline_influence: bool = False
    warnings: list[MLOpsWarning] = []
    recommended_operator_action: str | None = None


class MLOpsBlock(BaseModel):
    """Compact ML ops block for inclusion in the main /ops response."""
    total_models: int = 0
    active_models: int = 0
    shadow_models: int = 0
    latest_validation_status: str | None = None
    promotion_readiness: str | None = None
    warning_count: int = 0
    any_model_influences_live_pipeline: bool = False
    ml_is_shadow_only: bool = True
