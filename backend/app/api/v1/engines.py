"""Engine signal endpoints.

POST /api/v1/engines/run             — trigger engine run
GET  /api/v1/engines/latest-signals  — latest persisted signals
GET  /api/v1/engines/status          — engine layer status
GET  /api/v1/engines/definitions     — list engine definitions
GET  /api/v1/engines/comparison      — multi-engine comparison (backward compatible)
GET  /api/v1/engines/disagreement    — disagreement summary (backward compatible)
GET  /api/v1/engines/evidence        — evidence narrative (still partially derived)
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.schemas.engine import (
    EngineSignal, EngineComparisonResponse, DisagreementSummary,
    EngineDefinitionResponse, EngineSignalDetail,
    EngineRunRequest, EngineRunResult, EngineRunResponse, EngineRunDetailResponse,
    EngineStatusResponse,
)
from app.schemas.evidence import EvidenceItem, EvidenceNarrativeResponse
from app.models.recommendation import Recommendation
from app.models.signal import SignalRun, SignalOutput
from app.services.engines import EngineService

router = APIRouter()


# ── New real endpoints ────────────────────────────────────────────────

@router.post("/engines/run", response_model=ApiResponse[EngineRunResponse])
async def run_engines(body: EngineRunRequest, db: AsyncSession = Depends(get_db)):
    svc = EngineService(db)
    results = await svc.run_engines(
        feature_set_id=body.feature_set_id,
        engine_keys=body.engine_keys,
    )
    successful = sum(1 for r in results if r["status"] == "completed")
    failed = sum(1 for r in results if r["status"] == "failed")
    # Use actual resolved feature_set_id, not the request input (which may be None)
    actual_fs_id = next((r.get("feature_set_id") for r in results if r.get("feature_set_id")), body.feature_set_id)

    return ApiResponse(
        meta=make_meta(),
        data=EngineRunResponse(
            results=[EngineRunResult(**{k: v for k, v in r.items() if k in ("run_id", "engine_key", "status", "signal_count", "message")}) for r in results],
            total_engines=len(results),
            successful=successful,
            failed=failed,
            feature_set_id=actual_fs_id,
        ),
    )


@router.get("/engines/runs", response_model=ApiResponse[list[EngineRunDetailResponse]])
async def list_engine_runs(db: AsyncSession = Depends(get_db)):
    svc = EngineService(db)
    runs = await svc.get_runs()
    return ApiResponse(meta=make_meta(), data=[EngineRunDetailResponse(**r) for r in runs])


@router.get("/engines/runs/{run_id}", response_model=ApiResponse[EngineRunDetailResponse])
async def get_engine_run(run_id: str, db: AsyncSession = Depends(get_db)):
    svc = EngineService(db)
    r = await svc.get_run(run_id)
    if not r:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return ApiResponse(meta=make_meta(), data=EngineRunDetailResponse(**r))


@router.get("/engines/latest-signals", response_model=ApiResponse[list[EngineSignalDetail]])
async def get_latest_signals(db: AsyncSession = Depends(get_db)):
    svc = EngineService(db)
    signals = await svc.get_latest_signals()
    items = []
    for s in signals:
        arts = s.artifacts or {}
        items.append(EngineSignalDetail(
            engine_key=arts.get("engine_key", "unknown"),
            engine_name=arts.get("engine_name", "Unknown"),
            ticker=arts.get("ticker", "?"),
            asset_id=s.asset_id,
            stance=s.stance or "hold",
            score=s.score or 0.0,
            confidence=s.confidence or 0.0,
            risk_level=arts.get("risk_level", "Moderate"),
            drivers=arts.get("drivers", []),
            caveats=arts.get("caveats", []),
            source_feature_set_id=arts.get("source_feature_set_id"),
            feature_quality_summary=arts.get("feature_quality"),
            created_at=s.created_at,
        ))
    return ApiResponse(meta=make_meta(), data=items)


@router.get("/engines/status", response_model=ApiResponse[EngineStatusResponse])
async def get_engine_status(db: AsyncSession = Depends(get_db)):
    svc = EngineService(db)
    status = await svc.get_status()
    return ApiResponse(meta=make_meta(), data=EngineStatusResponse(**status))


@router.get("/engines/definitions", response_model=ApiResponse[list[EngineDefinitionResponse]])
async def list_engine_definitions(db: AsyncSession = Depends(get_db)):
    svc = EngineService(db)
    await svc.ensure_default_engines()
    from app.models.engine import EngineDefinition
    rows = (await db.execute(select(EngineDefinition).order_by(EngineDefinition.category))).scalars().all()
    return ApiResponse(meta=make_meta(), data=[
        EngineDefinitionResponse(
            id=d.id, key=d.key, name=d.name, category=d.category,
            description=d.description, version=d.version,
            required_feature_keys=d.required_feature_keys,
            output_kind=d.output_kind, is_active=d.is_active,
        ) for d in rows
    ])


# ── Backward-compatible endpoints (now from real DB signals) ──────────

def _build_engine_signal_from_outputs(engine_key: str, outputs: list[SignalOutput], eng_def: dict | None) -> EngineSignal:
    """Build an EngineSignal (comparison view) from real signal outputs."""
    if not outputs:
        return None
    # Average across assets for the comparison view
    avg_confidence = sum(o.confidence or 0 for o in outputs) / len(outputs)
    avg_score = sum(o.score or 0 for o in outputs) / len(outputs)
    arts = outputs[0].artifacts or {}

    # Determine dominant stance
    stances = [o.stance for o in outputs if o.stance]
    stance_counts = {}
    for s in stances:
        stance_counts[s] = stance_counts.get(s, 0) + 1
    dominant = max(stance_counts, key=stance_counts.get) if stance_counts else "hold"

    all_drivers = []
    for o in outputs:
        a = o.artifacts or {}
        all_drivers.extend(a.get("drivers", []))
    unique_drivers = list(dict.fromkeys(all_drivers))[:5]  # deduplicate, keep order

    all_caveats = []
    for o in outputs:
        a = o.artifacts or {}
        all_caveats.extend(a.get("caveats", []))
    unique_caveats = list(dict.fromkeys(all_caveats))[:3]

    return EngineSignal(
        engine_key=engine_key,
        engine_name=arts.get("engine_name", engine_key.replace("_", " ").title()),
        stance=dominant,
        confidence=round(avg_confidence, 2),
        weight=round(1.0 / 3, 2),  # equal weight among active engines
        risk_read=arts.get("risk_level", "Moderate"),
        horizon="3M",
        drivers=unique_drivers,
        ignores=unique_caveats,
        note=None,
    )


@router.get("/engines/comparison", response_model=ApiResponse[EngineComparisonResponse | None])
async def get_engine_comparison(db: AsyncSession = Depends(get_db)):
    rec = (await db.execute(
        select(Recommendation)
        .where(Recommendation.status.in_(["published", "published_with_warning", "staged", "deferred", "paper"]))
        .order_by(Recommendation.created_at.desc()).limit(1)
    )).scalar_one_or_none()
    if not rec:
        return ApiResponse(meta=make_meta(warnings=["No recommendation"]), data=None)

    svc = EngineService(db)
    all_signals = await svc.get_latest_signals()

    if not all_signals:
        return ApiResponse(meta=make_meta(warnings=["No engine signals available"]), data=None)

    # Group by engine_key
    by_engine: dict[str, list[SignalOutput]] = {}
    for s in all_signals:
        ek = (s.artifacts or {}).get("engine_key", "unknown")
        by_engine.setdefault(ek, []).append(s)

    engines = []
    for ek, outputs in by_engine.items():
        sig = _build_engine_signal_from_outputs(ek, outputs, None)
        if sig:
            engines.append(sig)

    if not engines:
        return ApiResponse(meta=make_meta(warnings=["No engine signals"]), data=None)

    # Compute synthesis
    total_weight = sum(e.weight for e in engines) or 1.0
    synth_conf = round(sum(e.confidence * e.weight for e in engines) / total_weight, 2)
    stance_counts = {}
    for e in engines:
        stance_counts[e.stance] = stance_counts.get(e.stance, 0) + 1
    dominant = max(stance_counts, key=stance_counts.get) if stance_counts else "hold"
    max_agree = max(stance_counts.values()) if stance_counts else 0
    dispersion = round(1 - max_agree / max(len(engines), 1), 2)

    return ApiResponse(
        meta=make_meta(),
        data=EngineComparisonResponse(
            recommendation_id=rec.id,
            engines=engines,
            synthesis_stance=dominant,
            synthesis_confidence=synth_conf,
            dispersion=dispersion,
        ),
    )


@router.get("/engines/disagreement", response_model=ApiResponse[DisagreementSummary | None])
async def get_disagreement(db: AsyncSession = Depends(get_db)):
    rec = (await db.execute(
        select(Recommendation)
        .where(Recommendation.status.in_(["published", "published_with_warning", "staged", "deferred", "paper"]))
        .order_by(Recommendation.created_at.desc()).limit(1)
    )).scalar_one_or_none()
    if not rec:
        return ApiResponse(meta=make_meta(warnings=["No recommendation"]), data=None)

    svc = EngineService(db)
    all_signals = await svc.get_latest_signals()
    if not all_signals:
        return ApiResponse(meta=make_meta(warnings=["No engine signals"]), data=None)

    # Group by engine, compute dominant stance per engine
    by_engine: dict[str, list[SignalOutput]] = {}
    for s in all_signals:
        ek = (s.artifacts or {}).get("engine_key", "unknown")
        by_engine.setdefault(ek, []).append(s)

    engine_stances = {}
    for ek, outputs in by_engine.items():
        stances = [o.stance for o in outputs if o.stance]
        if stances:
            sc = {}
            for st in stances:
                sc[st] = sc.get(st, 0) + 1
            engine_stances[ek] = max(sc, key=sc.get)
        else:
            engine_stances[ek] = "hold"

    total = len(engine_stances)
    stance_groups = {}
    for ek, st in engine_stances.items():
        stance_groups.setdefault(st, []).append(ek)

    dominant_stance = max(stance_groups, key=lambda s: len(stance_groups[s])) if stance_groups else "hold"
    agreeing = len(stance_groups.get(dominant_stance, []))
    dissenting = total - agreeing
    dissenting_engines_keys = [ek for st, eks in stance_groups.items() if st != dominant_stance for ek in eks]
    dispersion = round(1 - agreeing / max(total, 1), 2)

    # Resolve engine names
    defs = await svc._get_active_engines()
    name_map = {d.key: d.name for d in defs}
    dissenting_names = [name_map.get(ek, ek) for ek in dissenting_engines_keys]

    summary_parts = [f"{agreeing} of {total} engines agree on {dominant_stance} stance."]
    if dissenting_names:
        summary_parts.append(f"{dissenting} dissent: " + ", ".join(
            f"{n} ({engine_stances.get(ek, '?')})" for ek, n in zip(dissenting_engines_keys, dissenting_names)
        ) + ".")

    return ApiResponse(
        meta=make_meta(),
        data=DisagreementSummary(
            recommendation_id=rec.id,
            total_engines=total,
            agreeing=agreeing,
            dissenting=dissenting,
            dispersion=dispersion,
            dominant_stance=dominant_stance,
            dissenting_engines=dissenting_names,
            summary=" ".join(summary_parts),
        ),
    )


@router.get("/engines/evidence", response_model=ApiResponse[EvidenceNarrativeResponse | None])
async def get_evidence(db: AsyncSession = Depends(get_db)):
    """Evidence narrative — now derived from latest real signal outputs.

    Still partially structured (not a full NLP narrative), but no longer
    uses hardcoded EVIDENCE_ITEMS constants.
    """
    rec = (await db.execute(
        select(Recommendation)
        .where(Recommendation.status.in_(["published", "published_with_warning", "staged", "deferred", "paper"]))
        .order_by(Recommendation.created_at.desc()).limit(1)
    )).scalar_one_or_none()
    if not rec:
        return ApiResponse(meta=make_meta(warnings=["No recommendation"]), data=None)

    svc = EngineService(db)
    all_signals = await svc.get_latest_signals()

    if not all_signals:
        # Fallback: try importing legacy constants
        try:
            from seed import EVIDENCE_ITEMS
            items = [EvidenceItem(**ei) for ei in EVIDENCE_ITEMS]
            return ApiResponse(
                meta=make_meta(warnings=["Using legacy evidence items — no real engine signals available"]),
                data=EvidenceNarrativeResponse(
                    recommendation_id=rec.id, items=items,
                    caveat="Legacy evidence: engine runner has not produced real signals yet.",
                    last_refreshed_min=None,
                ),
            )
        except Exception:
            return ApiResponse(meta=make_meta(warnings=["No evidence available"]), data=None)

    # Build evidence items from real signal outputs
    by_engine: dict[str, list[SignalOutput]] = {}
    for s in all_signals:
        ek = (s.artifacts or {}).get("engine_key", "unknown")
        by_engine.setdefault(ek, []).append(s)

    items = []
    order = 1
    for ek, outputs in sorted(by_engine.items()):
        arts = outputs[0].artifacts or {} if outputs else {}
        drivers = arts.get("drivers", [])
        caveats = arts.get("caveats", [])
        avg_score = sum(o.score or 0 for o in outputs) / max(len(outputs), 1)
        avg_conf = sum(o.confidence or 0 for o in outputs) / max(len(outputs), 1)

        body_parts = drivers[:3] if drivers else ["No specific drivers identified"]
        if caveats:
            body_parts.append(f"Caveats: {'; '.join(caveats[:2])}")

        delta_label = f"{avg_score:+.2f}" if avg_score != 0 else "±0"
        delta_dir = "pos" if avg_score > 0.1 else "neg" if avg_score < -0.1 else "neutral"

        items.append(EvidenceItem(
            order=order,
            title=arts.get("engine_name", ek.replace("_", " ").title()),
            body=". ".join(body_parts) + ".",
            delta_label=delta_label,
            delta_direction=delta_dir,
            caveat=caveats[0] if caveats else None,
            source_engine=ek,
        ))
        order += 1

    return ApiResponse(
        meta=make_meta(),
        data=EvidenceNarrativeResponse(
            recommendation_id=rec.id,
            items=items,
            caveat=None,
            last_refreshed_min=None,
        ),
    )
