"""Ingestion endpoints.

POST /api/v1/ingest/bars       — trigger bar ingestion
POST /api/v1/ingest/news       — trigger news ingestion
GET  /api/v1/ingest/status     — ingestion freshness per source
GET  /api/v1/ingest/manifests  — list ingestion manifests
"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import get_current_user
from app.api.deps import make_meta
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.auth import User
from app.schemas.common import ApiResponse
from app.schemas.ingestion import (
    IngestBarsRequest,
    IngestionStatusResponse,
    IngestNewsRequest,
    IngestTriggerResult,
    ManifestListResponse,
    ManifestResponse,
    SourceFreshness,
)
from app.services.ingest import IngestService

router = APIRouter()


@router.post("/ingest/bars", response_model=ApiResponse[IngestTriggerResult])
@limiter.limit(settings.rate_limit_ingest)
async def trigger_bar_ingestion(
    request: Request,
    body: IngestBarsRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    svc = IngestService(db)
    manifest = await svc.ingest_bars(
        source=body.source,
        tickers=body.tickers,
        date_from=body.date_from,
        date_to=body.date_to,
    )
    return ApiResponse(
        meta=make_meta(),
        data=IngestTriggerResult(
            manifest_id=manifest.id,
            status=manifest.status,
            rows_ingested=manifest.row_count,
            message=f"Ingested {manifest.row_count} bars for {manifest.asset_count} assets",
        ),
    )


@router.post("/ingest/news", response_model=ApiResponse[IngestTriggerResult])
@limiter.limit(settings.rate_limit_ingest)
async def trigger_news_ingestion(
    request: Request,
    body: IngestNewsRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    svc = IngestService(db)
    manifest = await svc.ingest_news(
        source=body.source,
        date_from=body.date_from,
        date_to=body.date_to,
    )
    return ApiResponse(
        meta=make_meta(),
        data=IngestTriggerResult(
            manifest_id=manifest.id,
            status=manifest.status,
            rows_ingested=manifest.row_count,
            message=f"Ingested {manifest.row_count} news events",
        ),
    )


@router.get("/ingest/status", response_model=ApiResponse[IngestionStatusResponse])
async def get_ingestion_status(db: AsyncSession = Depends(get_db)):
    svc = IngestService(db)
    status = await svc.get_status()
    return ApiResponse(
        meta=make_meta(),
        data=IngestionStatusResponse(
            sources=[SourceFreshness(**s) for s in status["sources"]],
            total_bar_count=status["total_bar_count"],
            total_news_count=status["total_news_count"],
        ),
    )


@router.get("/ingest/manifests", response_model=ApiResponse[ManifestListResponse])
async def list_manifests(
    source: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    svc = IngestService(db)
    manifests = await svc.get_manifests(source)
    items = [
        ManifestResponse(
            id=m.id, source=m.source, kind=m.kind, status=m.status,
            asset_count=m.asset_count, row_count=m.row_count,
            date_from=m.date_from, date_to=m.date_to,
            started_at=m.started_at, completed_at=m.completed_at,
            error_message=m.error_message,
        )
        for m in manifests
    ]
    return ApiResponse(
        meta=make_meta(),
        data=ManifestListResponse(items=items, total=len(items)),
    )
