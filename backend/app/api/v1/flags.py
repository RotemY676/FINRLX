"""Feature flag endpoint (Phase MVP-4).

GET /api/v1/flags — return current feature-flag state so the frontend
can hide research/admin/RL surfaces for beta testers without a backend
redeploy.

The flags are sourced from `Settings` (env-var driven). Backend route
visibility is NOT gated by these flags today; the frontend uses them
to hide navigation. Future: add a `requires_feature(flag)` Depends()
if a hard backend gate becomes necessary.
"""
from fastapi import APIRouter

from app.api.deps import make_meta
from app.core.config import settings
from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/flags")
async def flags() -> ApiResponse[dict]:
    return ApiResponse(
        meta=make_meta(),
        data={
            "research_lane": settings.feature_research_lane,
            "paper_trading": settings.feature_paper_trading,
            "backtests": settings.feature_backtests,
            "replay": settings.feature_replay,
            "universe_ui": settings.feature_universe_ui,
            "ops_ui": settings.feature_ops_ui,
            "policy_ui": settings.feature_policy_ui,
            "integrations_ui": settings.feature_integrations_ui,
            "risk_ui": settings.feature_risk_ui,
            "news_ui": settings.feature_news_ui,
            "operator_console": settings.feature_operator_console,
        },
    )
