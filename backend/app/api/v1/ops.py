"""Ops Command Center endpoint.

GET /api/v1/ops — full ops dashboard data
Data matches design handoff: ops.jsx structures.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.schemas.ops import (
    OpsCommandCenterResponse, OpsQueueItem, OpsFeed, OpsEngine,
    OpsBreach, OpsIncident, OpsAuditEntry,
)
from app.models.ops import AuditEvent

router = APIRouter()

# Deterministic ops data matching design handoff ops.jsx
_QUEUE = [
    OpsQueueItem(recommendation_id="REC-NVDA-L", ticker="NVDA", stance="LONG", version="v4",
                 submitted_ago="12m", submitter="R. Mikhailov", weight="+4.2%", confidence=0.74,
                 flags=["sector cap"], priority="high"),
    OpsQueueItem(recommendation_id="REC-XOM-S", ticker="XOM", stance="SHORT", version="v2",
                 submitted_ago="22m", submitter="A. Chen", weight="−2.1%", confidence=0.68,
                 flags=["breach: oil 12%/10%"], priority="high"),
    OpsQueueItem(recommendation_id="REC-MSFT-T", ticker="MSFT", stance="TRIM", version="v3",
                 submitted_ago="8m", submitter="J. Park", weight="−0.9%", confidence=0.62,
                 flags=["Azure caveat"], priority="mid"),
    OpsQueueItem(recommendation_id="REC-AAPL-L", ticker="AAPL", stance="LONG", version="v2",
                 submitted_ago="84m", submitter="R. Mikhailov", weight="+1.8%", confidence=0.71,
                 flags=["stale"], priority="mid"),
]

_FEEDS = [
    OpsFeed(name="Reuters · news intel", status="ok", lag="0s", coverage="99.8%", slo=0.98),
    OpsFeed(name="Bloomberg · price feed", status="ok", lag="12ms", coverage="100%", slo=0.99),
    OpsFeed(name="Options flow · CBOE", status="degraded", lag="14m", coverage="72%", slo=0.86),
    OpsFeed(name="Earnings · Factset", status="ok", lag="3s", coverage="99.4%", slo=0.97),
    OpsFeed(name="Alt data · satellite", status="stale", lag="2.4h", coverage="41%", slo=0.64),
    OpsFeed(name="Fundamentals · internal", status="ok", lag="0s", coverage="100%", slo=1.0),
]

_ENGINES = [
    OpsEngine(name="Momentum", latency="82ms", drift=-0.03, last_run="2m", status="ok"),
    OpsEngine(name="Quality", latency="156ms", drift=0.01, last_run="2m", status="ok"),
    OpsEngine(name="Earnings revisions", latency="94ms", drift=-0.02, last_run="3m", status="ok"),
    OpsEngine(name="Value", latency="118ms", drift=0.08, last_run="2m", status="warn"),
    OpsEngine(name="Flow/options", latency="284ms", drift=-0.14, last_run="14m", status="degraded"),
]

_BREACHES = [
    OpsBreach(kind="sector", label="Semiconductors · 28.1% / 30%", utilization=0.937,
              trend="+0.8%", severity="high", related="NVDA promotion would add ~0.6%"),
    OpsBreach(kind="single", label="NVDA single-name · 4.2% / 5.0%", utilization=0.84,
              trend="+0.3%", severity="mid", related="Reviewed by J. Park · 12m ago"),
    OpsBreach(kind="oil", label="Energy net exposure · 12% / 10%", utilization=1.2,
              trend="+1.9%", severity="breach", related="Hard breach · escalated"),
]

_INCIDENTS = [
    OpsIncident(id="INC-003", title="Options flow feed — latency spike",
                started="14m ago", severity="sev-2", owner="M. Alvarez", status="investigating",
                affected_recs=11, note="Confidence capped for flow engine until recovery."),
    OpsIncident(id="INC-002", title="Alt-data satellite refresh failed",
                started="2h ago", severity="sev-3", owner="ops-bot", status="monitoring",
                affected_recs=0, note="Vendor acknowledged; next refresh 16:00 UTC."),
]


@router.get("/ops", response_model=ApiResponse[OpsCommandCenterResponse])
async def get_ops(db: AsyncSession = Depends(get_db)):
    # Audit trail from real DB
    events_result = await db.execute(
        select(AuditEvent).order_by(AuditEvent.occurred_at.desc()).limit(10)
    )
    audit_events = events_result.scalars().all()

    audit = []
    for ev in audit_events:
        details = ev.details or {}
        audit.append(OpsAuditEntry(
            when=details.get("ago", "?"),
            actor=ev.actor,
            action=ev.action,
            target=details.get("description", ev.action),
            scope=ev.object_type or "system",
            ok=True,
        ))

    return ApiResponse(
        meta=make_meta(),
        data=OpsCommandCenterResponse(
            queue=_QUEUE,
            feeds=_FEEDS,
            engines=_ENGINES,
            breaches=_BREACHES,
            incidents=_INCIDENTS,
            audit=audit,
        ),
    )
