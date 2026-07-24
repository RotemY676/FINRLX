"""Regime and activity endpoints.

GET /api/v1/regime — current regime snapshot
GET /api/v1/activity — recent activity feed
"""
import asyncio
import logging
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import get_current_user
from app.api.deps import make_meta
from app.core.database import get_db
from app.models.auth import User
from app.models.ops import AuditEvent
from app.schemas.common import ApiResponse
from app.schemas.regime import (
    ActivityEvent,
    ActivityFeedResponse,
    RegimeSnapshot,
)
from app.services.freshness_state import freshness_state_from_latest

logger = logging.getLogger(__name__)

router = APIRouter()


# The market-level view is the benchmark's own regime under the identical rule
# the per-ticker dossier uses, so the two can never disagree by construction.
REGIME_BENCHMARK = "SPY"
REGIME_HISTORY_DAYS = 420

# Named so a consumer can see exactly what is missing instead of inferring it
# from empty lists. These require models the system does not have.
_UNAVAILABLE = [
    "regime_confidence: no calibrated regime classifier exists",
    "alternatives: no probability model over alternative regimes exists",
    "signal_posture: no factor-exposure model exists",
    "sector_tilts: no sector-attribution model exists",
]


@router.get("/regime", response_model=ApiResponse[RegimeSnapshot])
async def get_regime():
    """Current regime for the benchmark, computed from real bars.

    Rebuilt 2026-07-23 (zero-fiction). The previous implementation returned a
    hardcoded label with an invented confidence, invented alternative-regime
    probabilities, invented factor sigmas and invented sector tilts. It was
    marked `is_demo=True`, but no consumer rendered that flag, so fabricated
    numbers reached the operator surface looking computed.

    Everything returned here is derived: the label from `autopilot.regime_label`
    (the same rule the dossier uses), and the switch date / persistence from
    `desk_payload.regime_band_series`, which replays that rule session by
    session. What cannot be computed is named in `unavailable`, not filled in.
    """
    from app.services.autopilot import regime_label
    from app.services.desk_payload import regime_band_series
    from app.services.single_ticker_analysis import fetch_history

    try:
        bars = await asyncio.to_thread(
            fetch_history, REGIME_BENCHMARK, REGIME_HISTORY_DAYS
        )
    except Exception as exc:  # noqa: BLE001 — provider boundary
        logger.warning("regime: benchmark history unavailable: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=(
                f"Regime needs {REGIME_BENCHMARK} history and the price source "
                "is unavailable. No regime is reported rather than a guess."
            ),
        ) from exc

    if not bars.closes:
        raise HTTPException(
            status_code=503,
            detail=f"No {REGIME_BENCHMARK} bars available to classify a regime.",
        )

    rule = regime_label(bars)
    bands = regime_band_series(bars)
    latest = bars.dates[-1]

    last_switch: str | None = None
    persistence: int | None = None
    # A single band means the rule never flipped inside the observed window —
    # the switch happened before it, so the date is unknown, not the window start.
    if len(bands) >= 2:
        last_switch = bands[-1]["start"]
        persistence = (latest - date.fromisoformat(last_switch)).days

    return ApiResponse(
        meta=make_meta(
            freshness=freshness_state_from_latest(latest),
            warnings=[
                f"Regime is the {REGIME_BENCHMARK} benchmark's rule-based label, "
                "not a market-wide model output."
            ],
        ),
        data=RegimeSnapshot(
            regime_label=rule["label"],
            regime_detail=rule["detail"],
            regime_kind=rule["kind"],
            benchmark=REGIME_BENCHMARK,
            persistence_days=persistence,
            last_switch_date=last_switch,
            sessions_observed=len(bars.closes),
            unavailable=_UNAVAILABLE,
            as_of=datetime(latest.year, latest.month, latest.day, tzinfo=UTC),
        ),
    )


@router.get("/activity", response_model=ApiResponse[ActivityFeedResponse])
async def get_activity(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Return recent activity feed from audit events.

    Gated at the function level (not the router): this reads the operator audit
    trail — tenant/operator state — so it stays authenticated even though its
    sibling ``/regime`` is intentionally public market context. See router.py.
    """
    events_result = await db.execute(
        select(AuditEvent).order_by(AuditEvent.occurred_at.desc()).limit(20)
    )
    audit_events = events_result.scalars().all()

    now = datetime.now(UTC)
    items = []
    for ev in audit_events:
        details = ev.details or {}
        ev_time = ev.occurred_at
        if ev_time.tzinfo is None:
            ev_time = ev_time.replace(tzinfo=UTC)
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
