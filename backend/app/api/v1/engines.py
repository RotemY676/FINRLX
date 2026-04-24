"""Engine signal endpoints.

GET /api/v1/engines/comparison — multi-engine comparison for current recommendation
GET /api/v1/engines/disagreement — disagreement summary
GET /api/v1/engines/evidence — evidence narrative
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.schemas.engine import EngineSignal, EngineComparisonResponse, DisagreementSummary
from app.schemas.evidence import EvidenceItem, EvidenceNarrativeResponse
from app.models.recommendation import Recommendation
from app.models.signal import SignalRun, SignalOutput

router = APIRouter()

# Evidence items stored in seed module — import at endpoint call time
from seed import EVIDENCE_ITEMS, ENGINE_DEFS


@router.get("/engines/comparison", response_model=ApiResponse[EngineComparisonResponse | None])
async def get_engine_comparison(db: AsyncSession = Depends(get_db)):
    rec = (await db.execute(
        select(Recommendation)
        .where(Recommendation.status.in_(["published", "published_with_warning"]))
        .order_by(Recommendation.published_at.desc()).limit(1)
    )).scalar_one_or_none()
    if not rec:
        return ApiResponse(meta=make_meta(warnings=["No published recommendation"]), data=None)

    # Get signal runs with their outputs
    runs = (await db.execute(
        select(SignalRun).order_by(SignalRun.engine_name)
    )).scalars().all()

    engines = []
    for run in runs:
        eng_def = next((e for e in ENGINE_DEFS if e["key"] == run.engine_name), None)
        if not eng_def:
            continue
        engines.append(EngineSignal(
            engine_key=run.engine_name,
            engine_name=eng_def["name"],
            stance=eng_def["stance"],
            confidence=eng_def["confidence"],
            weight=eng_def["weight"],
            risk_read=eng_def["risk"],
            horizon=eng_def["horizon"],
            drivers=eng_def["drivers"],
            ignores=eng_def["ignores"],
            note=eng_def["note"],
            data_freshness_min=eng_def["freshness_min"],
        ))

    buy_count = sum(1 for e in engines if e.stance == "buy")
    total = len(engines)
    dominant = "buy" if buy_count > total / 2 else "hold"
    dispersion = round(1 - (max(sum(1 for e in engines if e.stance == s) for s in ["buy", "hold", "sell"]) / max(total, 1)), 2)

    return ApiResponse(
        meta=make_meta(),
        data=EngineComparisonResponse(
            recommendation_id=rec.id,
            engines=engines,
            synthesis_stance=dominant,
            synthesis_confidence=round(sum(e.confidence * e.weight for e in engines) / max(sum(e.weight for e in engines), 0.01), 2),
            dispersion=dispersion,
        ),
    )


@router.get("/engines/disagreement", response_model=ApiResponse[DisagreementSummary | None])
async def get_disagreement(db: AsyncSession = Depends(get_db)):
    rec = (await db.execute(
        select(Recommendation)
        .where(Recommendation.status.in_(["published", "published_with_warning"]))
        .order_by(Recommendation.published_at.desc()).limit(1)
    )).scalar_one_or_none()
    if not rec:
        return ApiResponse(meta=make_meta(warnings=["No published recommendation"]), data=None)

    buy_engines = [e for e in ENGINE_DEFS if e["stance"] == "buy"]
    non_buy = [e for e in ENGINE_DEFS if e["stance"] != "buy"]
    total = len(ENGINE_DEFS)
    agreeing = len(buy_engines)
    dissenting = len(non_buy)

    return ApiResponse(
        meta=make_meta(),
        data=DisagreementSummary(
            recommendation_id=rec.id,
            total_engines=total,
            agreeing=agreeing,
            dissenting=dissenting,
            dispersion=0.37,
            dominant_stance="buy",
            dissenting_engines=[e["name"] for e in non_buy],
            summary=f"{agreeing} of {total} engines agree on buy stance. {dissenting} engines dissent: "
                    + ", ".join(f'{e["name"]} ({e["stance"]})' for e in non_buy)
                    + ".",
        ),
    )


@router.get("/engines/evidence", response_model=ApiResponse[EvidenceNarrativeResponse | None])
async def get_evidence(db: AsyncSession = Depends(get_db)):
    rec = (await db.execute(
        select(Recommendation)
        .where(Recommendation.status.in_(["published", "published_with_warning"]))
        .order_by(Recommendation.published_at.desc()).limit(1)
    )).scalar_one_or_none()
    if not rec:
        return ApiResponse(meta=make_meta(warnings=["No published recommendation"]), data=None)

    items = [EvidenceItem(**ei) for ei in EVIDENCE_ITEMS]

    return ApiResponse(
        meta=make_meta(),
        data=EvidenceNarrativeResponse(
            recommendation_id=rec.id,
            items=items,
            caveat="Attribution unavailable for the fundamentals engine — it served a fallback path during the 09:20 data lag. Evidence above reflects the primary model only.",
            last_refreshed_min=12,
        ),
    )
