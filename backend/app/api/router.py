"""Central API router. All v1 routes are registered here."""
from fastapi import APIRouter

from app.api.v1.overview import router as overview_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.decision import router as decision_router
from app.api.v1.comparison import router as comparison_router
from app.api.v1.replay import router as replay_router
from app.api.v1.backtests import router as backtests_router
from app.api.v1.paper import router as paper_router
from app.api.v1.engines import router as engines_router
from app.api.v1.regime import router as regime_router
from app.api.v1.health import router as health_router

api_router = APIRouter()

api_router.include_router(overview_router, tags=["overview"])
api_router.include_router(recommendations_router, tags=["recommendations"])
api_router.include_router(decision_router, tags=["decision"])
api_router.include_router(comparison_router, tags=["comparison"])
api_router.include_router(replay_router, tags=["replay"])
api_router.include_router(backtests_router, tags=["backtests"])
api_router.include_router(paper_router, tags=["paper"])
api_router.include_router(engines_router, tags=["engines"])
api_router.include_router(regime_router, tags=["regime"])
api_router.include_router(health_router, tags=["health"])
