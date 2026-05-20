"""Replay endpoints.

GET /api/v1/replay                         — list replay snapshots
GET /api/v1/replay/{recommendation_id}     — full replay for a recommendation
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import make_meta
from app.core.database import get_db
from app.models.recommendation import Recommendation, RecommendationWeight
from app.models.reference import Asset
from app.models.validation import ReplaySnapshot
from app.schemas.common import ApiResponse
from app.schemas.recommendation import ConfidenceTriplet, WeightEntry
from app.schemas.replay import (
    ReplayDetail,
    ReplayListItem,
    ReplayListResponse,
    ReplayStageSnapshot,
)
from app.services.replay import ReplayService

router = APIRouter()


@router.get("/replay", response_model=ApiResponse[ReplayListResponse])
async def list_replays(db: AsyncSession = Depends(get_db)):
    """List recommendations that have replay snapshots. Auto-create for pipeline recs."""
    replay_svc = ReplayService(db)

    # Auto-create replay snapshots for pipeline-generated recommendations that lack them
    pipeline_recs = (await db.execute(
        select(Recommendation.id)
        .where(Recommendation.source_feature_set_id.is_not(None))
        .order_by(Recommendation.created_at.desc())
        .limit(20)
    )).scalars().all()
    for rec_id in pipeline_recs:
        await replay_svc.ensure_replay_exists(rec_id)

    # Get distinct recommendation_ids with their latest snapshot
    stmt = (
        select(
            ReplaySnapshot.recommendation_id,
            func.max(ReplaySnapshot.captured_at).label("latest"),
            func.count(ReplaySnapshot.id).label("stage_count"),
        )
        .group_by(ReplaySnapshot.recommendation_id)
        .order_by(func.max(ReplaySnapshot.captured_at).desc())
    )
    rows = (await db.execute(stmt)).all()

    items = []
    for rec_id, latest, _stage_count in rows:
        rec = (await db.execute(
            select(Recommendation).where(Recommendation.id == rec_id)
        )).scalar_one_or_none()

        weight_count = (await db.execute(
            select(func.count()).select_from(RecommendationWeight)
            .where(RecommendationWeight.recommendation_id == rec_id)
        )).scalar() or 0

        items.append(ReplayListItem(
            id=rec_id,
            recommendation_id=rec_id,
            captured_at=latest,
            status=rec.status if rec else "unknown",
            total_positions=weight_count,
            model_confidence=rec.model_confidence if rec else None,
        ))

    return ApiResponse(
        meta=make_meta(),
        data=ReplayListResponse(items=items, total=len(items)),
    )


@router.get("/replay/{recommendation_id}", response_model=ApiResponse[ReplayDetail | None])
async def get_replay(recommendation_id: str, db: AsyncSession = Depends(get_db)):
    """Full replay for a specific recommendation. Auto-creates snapshots if missing."""
    rec = (await db.execute(
        select(Recommendation).where(Recommendation.id == recommendation_id)
    )).scalar_one_or_none()
    if not rec:
        return ApiResponse(meta=make_meta(warnings=["Recommendation not found"]), data=None)

    # Auto-create replay if pipeline-generated and no snapshots exist
    replay_svc = ReplayService(db)
    await replay_svc.ensure_replay_exists(recommendation_id)

    # Get snapshots
    snapshots = (await db.execute(
        select(ReplaySnapshot)
        .where(ReplaySnapshot.recommendation_id == recommendation_id)
        .order_by(ReplaySnapshot.captured_at)
    )).scalars().all()

    if not snapshots:
        return ApiResponse(meta=make_meta(warnings=["No replay snapshots found"]), data=None)

    # Get weights with asset info
    weights_stmt = (
        select(RecommendationWeight, Asset.ticker, Asset.name)
        .outerjoin(Asset, RecommendationWeight.asset_id == Asset.id)
        .where(RecommendationWeight.recommendation_id == recommendation_id)
        .order_by(RecommendationWeight.target_weight.desc())
    )
    weight_rows = (await db.execute(weights_stmt)).all()
    weight_entries = [
        WeightEntry(
            asset_id=w.asset_id, ticker=ticker or "???", name=name or "Unknown",
            target_weight=w.target_weight, previous_weight=w.previous_weight,
            delta=w.delta, stance=w.stance, rationale=w.rationale,
        )
        for w, ticker, name in weight_rows
    ]

    warning_list = rec.warnings if isinstance(rec.warnings, list) else []
    is_pipeline = rec.source_feature_set_id is not None
    if not is_pipeline:
        warning_list = warning_list + ["This replay is from seeded/demo data, not a real pipeline run"]

    return ApiResponse(
        meta=make_meta(),
        data=ReplayDetail(
            id=snapshots[0].id,
            recommendation_id=recommendation_id,
            captured_at=snapshots[-1].captured_at,
            status=rec.status,
            confidence=ConfidenceTriplet(
                model_confidence=rec.model_confidence,
                data_confidence=rec.data_confidence,
                operational_confidence=rec.operational_confidence,
            ),
            weights=weight_entries,
            rationale_summary=rec.rationale_summary,
            warnings=warning_list,
            data_as_of=rec.data_as_of,
            stages=[
                ReplayStageSnapshot(
                    stage=s.stage, snapshot_data=s.snapshot_data or {},
                    captured_at=s.captured_at,
                )
                for s in snapshots
            ],
        ),
    )
