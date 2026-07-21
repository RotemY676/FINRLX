"""Unified readiness aggregation (US-P0-08).

Composes existing per-domain signals — market-data (price) freshness, FX
freshness, and provider configuration — into a single operator readiness report
with an explicit overall verdict and the affected scope for anything not ready.

Fail-closed by construction: each component is evaluated inside its own guard;
if evaluation raises, that component is reported ``unavailable`` with the reason
rather than being silently omitted or treated as ready. The overall status is
the worst component status.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.readiness import (
    READINESS_STATUSES,
    ReadinessComponent,
    ReadinessReport,
)
from app.services import fx_freshness, price_freshness
from app.services.integrations import IntegrationsService

_RANK = {status: i for i, status in enumerate(READINESS_STATUSES)}


def _worst(statuses: list[str]) -> str:
    if not statuses:
        return "unavailable"
    return max(statuses, key=lambda s: _RANK.get(s, len(_RANK)))


async def _price_component(db: AsyncSession, now: datetime) -> ReadinessComponent:
    report = await price_freshness.evaluate_price_freshness(db, now=now)
    total = len(report.tickers)
    if total == 0:
        return ReadinessComponent(
            name="market_data",
            status="unavailable",
            detail="no ingested price bars",
        )
    affected = [tf.ticker for tf in (report.stale + report.degraded)]
    status = "degraded" if affected else "ready"
    return ReadinessComponent(
        name="market_data",
        status=status,
        detail=None if status == "ready" else "stale or degraded tickers present",
        affected=sorted(affected),
        metrics={
            "tickers": total,
            "stale": len(report.stale),
            "degraded": len(report.degraded),
        },
    )


async def _fx_component(db: AsyncSession, now: datetime) -> ReadinessComponent:
    report = await fx_freshness.evaluate_freshness(db, now=now)
    total = len(report.pairs)
    if total == 0:
        return ReadinessComponent(
            name="fx",
            status="unavailable",
            detail="no fx rates ingested",
        )
    affected = [f"{p.base}/{p.quote}" for p in report.stale_pairs]
    status = "degraded" if affected else "ready"
    return ReadinessComponent(
        name="fx",
        status=status,
        detail=None if status == "ready" else "stale fx pairs present",
        affected=sorted(affected),
        metrics={"pairs": total, "stale": len(report.stale_pairs)},
    )


async def _provider_component(db: AsyncSession) -> ReadinessComponent:
    readiness = await IntegrationsService(db).get_provider_readiness()
    ready_for_pipeline = bool(readiness.get("ready_for_pipeline"))
    degraded = int(readiness.get("degraded", 0) or 0)
    if not ready_for_pipeline:
        status = "unavailable"
        detail = "no completed ingestion manifests"
    elif degraded > 0:
        status = "degraded"
        detail = "one or more providers degraded or stale"
    else:
        status = "ready"
        detail = None
    return ReadinessComponent(
        name="providers",
        status=status,
        detail=detail,
        metrics={
            "real_providers": int(readiness.get("real_providers", 0) or 0),
            "healthy": int(readiness.get("healthy", 0) or 0),
            "degraded": degraded,
            "completed_manifests": int(readiness.get("completed_manifests", 0) or 0),
        },
    )


async def _guarded(name: str, coro) -> ReadinessComponent:
    """Run a component evaluator fail-closed: any error → unavailable."""
    try:
        return await coro
    except Exception as exc:  # noqa: BLE001 — readiness must never crash; fail closed
        return ReadinessComponent(
            name=name,
            status="unavailable",
            detail=f"evaluation failed: {str(exc)[:160]}",
        )


async def build_readiness(db: AsyncSession, now: datetime) -> ReadinessReport:
    components = [
        await _guarded("market_data", _price_component(db, now)),
        await _guarded("fx", _fx_component(db, now)),
        await _guarded("providers", _provider_component(db)),
    ]
    overall = _worst([c.status for c in components])
    return ReadinessReport(
        generated_at=now,
        overall=overall,
        ready=overall == "ready",
        components=components,
    )
