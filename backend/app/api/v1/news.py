"""Phase B2 — News intelligence endpoint.

GET /api/v1/news  — headlines from RSS sources, scored with VADER sentiment.
"""
from fastapi import APIRouter, Query

from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.services.news import NewsService

router = APIRouter()


@router.get("/news", response_model=ApiResponse[dict])
async def get_news(refresh: bool = Query(False, description="Bypass the 5-minute cache")):
    svc = NewsService()
    items = await svc.get_headlines(force_refresh=refresh)
    summary = svc.get_summary(items)
    return ApiResponse(
        meta=make_meta(),
        data={
            "summary": summary,
            "items": [i.as_dict() for i in items],
        },
    )
