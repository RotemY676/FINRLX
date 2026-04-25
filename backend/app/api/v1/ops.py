"""Ops Command Center endpoints.

GET  /api/v1/ops                    — full ops dashboard data (DB-backed)
GET  /api/v1/ops/queue              — publication queue (filterable)
GET  /api/v1/ops/feeds              — data feed status
GET  /api/v1/ops/engines            — engine health (computed from signal_runs)
GET  /api/v1/ops/breaches           — active policy breaches
GET  /api/v1/ops/incidents          — open incidents
GET  /api/v1/ops/audit              — audit trail (filterable by scope)
POST /api/v1/ops/queue/{id}/approve — approve queue item
POST /api/v1/ops/queue/{id}/defer   — defer queue item
POST /api/v1/ops/queue/{id}/challenge — challenge queue item
GET  /api/v1/workspace-counts       — badge counts for sidebar
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.schemas.ops import (
    OpsCommandCenterResponse, OpsQueueItem, OpsFeed, OpsEngine,
    OpsBreach, OpsIncident, OpsAuditEntry, OpsSystemKpi,
    QueueActionResponse, WorkspaceCounts, OpsMLBlock,
)
from app.models.ops import (
    AuditEvent, Incident, DataFeed, PolicyBreach, PublicationQueueEntry,
)
from app.models.signal import SignalRun

router = APIRouter()


# ── Helpers ──────────────────────────────────────────────────────────

async def _query_queue(db: AsyncSession, filter_: str = "all") -> list[OpsQueueItem]:
    stmt = select(PublicationQueueEntry).where(PublicationQueueEntry.status == "pending")
    if filter_ == "high":
        stmt = stmt.where(PublicationQueueEntry.priority == "high")
    stmt = stmt.order_by(PublicationQueueEntry.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return [
        OpsQueueItem(
            id=r.id, recommendation_id=r.recommendation_id, ticker=r.ticker,
            stance=r.stance, version=r.version, submitted_ago=r.submitted_ago,
            submitter=r.submitter, weight=r.weight, confidence=r.confidence,
            flags=r.flags or [], priority=r.priority, status=r.status,
        )
        for r in rows
    ]


async def _query_feeds(db: AsyncSession) -> list[OpsFeed]:
    rows = (await db.execute(select(DataFeed).order_by(DataFeed.name))).scalars().all()
    return [
        OpsFeed(name=r.name, status=r.status, lag=r.lag, coverage=r.coverage, slo=r.slo)
        for r in rows
    ]


async def _query_engines(db: AsyncSession) -> list[OpsEngine]:
    """Compute engine health from the latest SignalRun per engine, including drift."""
    from app.models.signal import SignalOutput

    now = datetime.now(timezone.utc)
    # Get the latest run per engine
    subq = (
        select(
            SignalRun.engine_name,
            func.max(SignalRun.run_completed_at).label("latest"),
        )
        .where(SignalRun.status == "completed")
        .group_by(SignalRun.engine_name)
        .subquery()
    )
    stmt = (
        select(SignalRun)
        .join(subq, (SignalRun.engine_name == subq.c.engine_name) & (SignalRun.run_completed_at == subq.c.latest))
    )
    rows = (await db.execute(stmt)).scalars().all()

    # Pre-compute drift: avg confidence of latest run vs previous run per engine
    drift_map: dict[str, float] = {}
    for r in rows:
        # Get avg confidence for this run
        latest_avg_result = await db.execute(
            select(func.avg(SignalOutput.confidence)).where(SignalOutput.signal_run_id == r.id)
        )
        latest_avg = latest_avg_result.scalar() or 0.0

        # Get the previous run for this engine
        prev_run_result = await db.execute(
            select(SignalRun.id)
            .where(SignalRun.engine_name == r.engine_name, SignalRun.status == "completed", SignalRun.id != r.id)
            .order_by(SignalRun.run_completed_at.desc())
            .limit(1)
        )
        prev_run_id = prev_run_result.scalar()

        if prev_run_id:
            prev_avg_result = await db.execute(
                select(func.avg(SignalOutput.confidence)).where(SignalOutput.signal_run_id == prev_run_id)
            )
            prev_avg = prev_avg_result.scalar() or 0.0
            drift_map[r.engine_name] = round(latest_avg - prev_avg, 2)
        else:
            drift_map[r.engine_name] = 0.0

    engines = []
    for r in rows:
        latency_ms = 0
        if r.run_started_at and r.run_completed_at:
            latency_ms = int((r.run_completed_at - r.run_started_at).total_seconds() * 1000)
        mins_ago = int((now - r.run_completed_at.replace(tzinfo=timezone.utc)).total_seconds() / 60) if r.run_completed_at else 999

        # Status based on staleness
        if mins_ago > 10:
            status = "degraded"
        elif mins_ago > 5:
            status = "warn"
        else:
            status = "ok"

        drift = drift_map.get(r.engine_name, 0.0)

        engines.append(OpsEngine(
            name=r.engine_name.replace("_", " ").title(),
            latency=f"{latency_ms}ms",
            drift=drift,
            last_run=f"{mins_ago}m",
            status=status,
        ))

    return engines


async def _query_breaches(db: AsyncSession) -> list[OpsBreach]:
    rows = (await db.execute(
        select(PolicyBreach).where(PolicyBreach.is_active == True).order_by(PolicyBreach.severity)  # noqa: E712
    )).scalars().all()
    return [
        OpsBreach(
            kind=r.kind, label=r.label, utilization=r.utilization,
            trend=r.trend, severity=r.severity, related=r.related or "",
        )
        for r in rows
    ]


async def _query_incidents(db: AsyncSession) -> list[OpsIncident]:
    rows = (await db.execute(
        select(Incident).where(Incident.status != "resolved").order_by(Incident.created_at.desc())
    )).scalars().all()
    return [
        OpsIncident(
            id=r.id[:8], title=r.title, started="recent",
            severity=f"sev-{r.severity}", owner=r.source or "unknown",
            status=r.status, affected_recs=0, note=r.description or "",
        )
        for r in rows
    ]


async def _query_audit(db: AsyncSession, scope: str = "all") -> list[OpsAuditEntry]:
    stmt = select(AuditEvent).order_by(AuditEvent.occurred_at.desc()).limit(20)
    if scope != "all":
        stmt = stmt.where(AuditEvent.object_type == scope)
    rows = (await db.execute(stmt)).scalars().all()
    return [
        OpsAuditEntry(
            when=(ev.details or {}).get("ago", "?"),
            actor=ev.actor,
            action=ev.action,
            target=(ev.details or {}).get("description", ev.action),
            scope=ev.object_type or "system",
            ok=True,
        )
        for ev in rows
    ]


def _compute_kpis(
    queue: list[OpsQueueItem], feeds: list[OpsFeed],
    breaches: list[OpsBreach], incidents: list[OpsIncident],
    engines: list[OpsEngine],
) -> list[OpsSystemKpi]:
    ok_feeds = sum(1 for f in feeds if f.status == "ok")
    total_feeds = len(feeds)
    feed_pct = f"{ok_feeds}/{total_feeds}" if total_feeds > 0 else "0/0"

    ok_engines = sum(1 for e in engines if e.status == "ok")
    total_engines = len(engines)

    hard_breaches = sum(1 for b in breaches if b.severity == "breach")

    return [
        OpsSystemKpi(key="Queue depth", value=str(len(queue)), sub="pending items",
                     tone="caution" if len(queue) > 5 else "neutral"),
        OpsSystemKpi(key="Feed coverage", value=feed_pct, sub="feeds healthy",
                     tone="pos" if ok_feeds == total_feeds else "caution"),
        OpsSystemKpi(key="Engine health", value=f"{ok_engines}/{total_engines}", sub="engines ok",
                     tone="pos" if ok_engines == total_engines else "caution"),
        OpsSystemKpi(key="Policy breaches", value=str(hard_breaches), sub="hard breaches",
                     tone="breach" if hard_breaches > 0 else "pos"),
        OpsSystemKpi(key="Open incidents", value=str(len(incidents)), sub="unresolved",
                     tone="caution" if len(incidents) > 0 else "pos"),
        OpsSystemKpi(key="High priority", value=str(sum(1 for q in queue if q.priority == "high")),
                     sub="queue items", tone="breach" if any(q.priority == "high" for q in queue) else "neutral"),
    ]


# ── Main endpoint ────────────────────────────────────────────────────

@router.get("/ops", response_model=ApiResponse[OpsCommandCenterResponse])
async def get_ops(db: AsyncSession = Depends(get_db)):
    queue = await _query_queue(db)
    feeds = await _query_feeds(db)
    engines = await _query_engines(db)
    breaches = await _query_breaches(db)
    incidents = await _query_incidents(db)
    audit = await _query_audit(db)
    kpis = _compute_kpis(queue, feeds, breaches, incidents, engines)

    # ML ops block
    from app.services.ml_ops import MLOpsService
    ml_svc = MLOpsService(db)
    ml_block_data = await ml_svc.get_ops_ml_block()
    ml_block = OpsMLBlock(**ml_block_data)

    return ApiResponse(
        meta=make_meta(),
        data=OpsCommandCenterResponse(
            queue=queue, feeds=feeds, engines=engines,
            breaches=breaches, incidents=incidents, audit=audit,
            system_kpis=kpis, ml_ops=ml_block,
        ),
    )


# ── Sub-endpoints ────────────────────────────────────────────────────

@router.get("/ops/queue", response_model=ApiResponse[list[OpsQueueItem]])
async def get_ops_queue(
    filter: str = Query("all", pattern="^(all|high|mine)$"),
    db: AsyncSession = Depends(get_db),
):
    return ApiResponse(meta=make_meta(), data=await _query_queue(db, filter))


@router.get("/ops/feeds", response_model=ApiResponse[list[OpsFeed]])
async def get_ops_feeds(db: AsyncSession = Depends(get_db)):
    return ApiResponse(meta=make_meta(), data=await _query_feeds(db))


@router.get("/ops/engines", response_model=ApiResponse[list[OpsEngine]])
async def get_ops_engines(db: AsyncSession = Depends(get_db)):
    return ApiResponse(meta=make_meta(), data=await _query_engines(db))


@router.get("/ops/breaches", response_model=ApiResponse[list[OpsBreach]])
async def get_ops_breaches(db: AsyncSession = Depends(get_db)):
    return ApiResponse(meta=make_meta(), data=await _query_breaches(db))


@router.get("/ops/incidents", response_model=ApiResponse[list[OpsIncident]])
async def get_ops_incidents(db: AsyncSession = Depends(get_db)):
    return ApiResponse(meta=make_meta(), data=await _query_incidents(db))


@router.get("/ops/audit", response_model=ApiResponse[list[OpsAuditEntry]])
async def get_ops_audit(
    scope: str = Query("all", pattern="^(all|recommendation|policy|engine|system|breach|incident|backtest|note|defer|publish)$"),
    db: AsyncSession = Depends(get_db),
):
    return ApiResponse(meta=make_meta(), data=await _query_audit(db, scope))


# ── Queue actions ────────────────────────────────────────────────────

async def _queue_action(db: AsyncSession, item_id: str, new_status: str, action_label: str) -> QueueActionResponse:
    result = await db.execute(select(PublicationQueueEntry).where(PublicationQueueEntry.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail=f"Queue item {item_id} not found")

    item.status = new_status
    db.add(AuditEvent(
        actor="current_user",
        action=action_label,
        object_type="recommendation",
        object_id=item.recommendation_id,
        details={"description": f"{action_label} {item.ticker} {item.stance}", "ago": "now"},
    ))
    await db.commit()
    return QueueActionResponse(id=item_id, new_status=new_status, message=f"{item.ticker} {new_status}")


@router.post("/ops/queue/{item_id}/approve", response_model=ApiResponse[QueueActionResponse])
async def approve_queue_item(item_id: str, db: AsyncSession = Depends(get_db)):
    data = await _queue_action(db, item_id, "approved", "approve")
    return ApiResponse(meta=make_meta(), data=data)


@router.post("/ops/queue/{item_id}/defer", response_model=ApiResponse[QueueActionResponse])
async def defer_queue_item(item_id: str, db: AsyncSession = Depends(get_db)):
    data = await _queue_action(db, item_id, "deferred", "defer")
    return ApiResponse(meta=make_meta(), data=data)


@router.post("/ops/queue/{item_id}/challenge", response_model=ApiResponse[QueueActionResponse])
async def challenge_queue_item(item_id: str, db: AsyncSession = Depends(get_db)):
    data = await _queue_action(db, item_id, "challenged", "challenge")
    return ApiResponse(meta=make_meta(), data=data)


# ── Incident resolve ──────────────────────────────────────────────────

@router.post("/ops/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    inc = result.scalar_one_or_none()
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    inc.status = "resolved"
    inc.resolved_at = datetime.now(timezone.utc)
    db.add(AuditEvent(
        actor="current_user", action="resolve_incident",
        object_type="incident", object_id=incident_id,
        details={"description": f"Resolved incident: {inc.title}", "ago": "now"},
    ))
    await db.commit()
    return ApiResponse(
        meta=make_meta(),
        data={"success": True, "message": f"Incident {incident_id} resolved"},
    )


# ── Workspace counts ─────────────────────────────────────────────────

@router.get("/workspace-counts", response_model=ApiResponse[WorkspaceCounts])
async def get_workspace_counts(db: AsyncSession = Depends(get_db)):
    from app.models.recommendation import Recommendation

    # Overview: pending (non-published) recommendations
    overview_count = (await db.execute(
        select(func.count()).select_from(PublicationQueueEntry).where(PublicationQueueEntry.status == "pending")
    )).scalar() or 0

    # Decisions: total active recommendations
    decisions_count = (await db.execute(
        select(func.count()).select_from(Recommendation)
    )).scalar() or 0

    # Risk: active policy breaches
    risk_count = (await db.execute(
        select(func.count()).select_from(PolicyBreach).where(PolicyBreach.is_active == True)  # noqa: E712
    )).scalar() or 0

    # Ops: open incidents
    ops_count = (await db.execute(
        select(func.count()).select_from(Incident).where(Incident.status != "resolved")
    )).scalar() or 0

    return ApiResponse(
        meta=make_meta(),
        data=WorkspaceCounts(
            overview=overview_count,
            decisions=decisions_count,
            risk=risk_count,
            ops=ops_count,
        ),
    )
