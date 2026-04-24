"""Overview endpoint schema.

Maps to API Contract doc 12: GET /api/v1/overview.
"""
from datetime import datetime

from pydantic import BaseModel

from app.schemas.recommendation import RecommendationSummary, ConfidenceTriplet


class HealthSummary(BaseModel):
    source_freshness_ok: bool = True
    feature_health_ok: bool = True
    model_health_ok: bool = True
    publication_health_ok: bool = True
    open_incidents: int = 0
    last_checked_at: datetime | None = None


class OverviewResponse(BaseModel):
    current_recommendation: RecommendationSummary | None = None
    health: HealthSummary
    recent_recommendation_count: int = 0
    last_published_at: datetime | None = None
