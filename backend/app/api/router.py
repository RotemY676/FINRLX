"""Central API router. All v1 routes are registered here."""
from fastapi import APIRouter

from app.api.v1.overview import router as overview_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.health import router as health_router

api_router = APIRouter()

api_router.include_router(overview_router, tags=["overview"])
api_router.include_router(recommendations_router, tags=["recommendations"])
api_router.include_router(health_router, tags=["health"])
