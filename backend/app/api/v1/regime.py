"""Regime and activity endpoints.

GET /api/v1/regime — current regime snapshot
GET /api/v1/activity — recent activity feed
"""
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.schemas.regime import (
    RegimeSnapshot, SignalPosture, SectorTilt,
    ActivityFeedResponse, ActivityEvent,
)
from app.models.ops import AuditEvent

router = APIRouter()


@router.get("/regime", response_model=ApiResponse[RegimeSnapshot])
async def get_regime():
    """Return current regime classification. Seeded deterministic data."""
    now = datetime.now(timezone.utc)
    return ApiResponse(
        meta=make_meta(),
        data=RegimeSnapshot(
            regime_label="Risk-on · late-cycle",
            regime_confidence=0.78,
            persistence_days=41,
            last_switch_date="2026-03-14",
            alternatives=[
                {"label": "risk-off", "prob": 0.14},
                {"label": "rotation", "prob": 0.08},
            ],
            signal_posture=[
                SignalPosture(factor="Momentum", direction="overweight", sigma=2.4),
                SignalPosture(factor="Quality", direction="overweight", sigma=1.1),
                SignalPosture(factor="Value", direction="neutral", sigma=0.0),
                SignalPosture(factor="Low-vol", direction="underweight", sigma=-1.8),
            ],
            sector_tilts=[
                SectorTilt(sector="Semis", tilt_pct=3.2),
                SectorTilt(sector="Software", tilt_pct=2.1),
                SectorTilt(sector="Financials", tilt_pct=0.4),
                SectorTilt(sector="Energy", tilt_pct=-1.6),
                SectorTilt(sector="Utilities", tilt_pct=-2.4),
            ],
            as_of=now,
        ),
    )


@router.get("/activity", response_model=ApiResponse[ActivityFeedResponse])
async def get_activity(db: AsyncSession = Depends(get_db)):
    """Return recent activity feed from audit events."""
    events_result = await db.execute(
        select(AuditEvent).order_by(AuditEvent.occurred_at.desc()).limit(20)
    )
    audit_events = events_result.scalars().all()

    now = datetime.now(timezone.utc)
    items = []
    for ev in audit_events:
        details = ev.details or {}
        ev_time = ev.occurred_at
        if ev_time.tzinfo is None:
            ev_time = ev_time.replace(tzinfo=timezone.utc)
        secs = max((now - ev_time).total_seconds(), 0)
        when_ago = f"{int(secs / 60)}m" if secs < 3600 else f"{int(secs / 3600)}h"

        items.append(ActivityEvent(
            kind=ev.action,
            actor=ev.actor,
            description=details.get("description", ev.action),
            detail=details.get("detail"),
            when_ago=when_ago,
            timestamp=ev_time,
        ))

    return ApiResponse(
        meta=make_meta(),
        data=ActivityFeedResponse(events=items, total=len(items)),
    )
