"""Replay service.

Phase 5B: creates and queries replay snapshots for pipeline/backtest decisions.
Captures stage-by-stage decision state for forensic reconstruction.
"""
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.validation import ReplaySnapshot
from app.models.recommendation import Recommendation, RecommendationWeight
from app.models.decision_pipeline import SelectionRun, AllocationResult, TimingResult, RiskOverlayResult
from app.models.base import gen_uuid


class ReplayService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_replay_for_recommendation(self, recommendation_id: str) -> list[ReplaySnapshot]:
        """Create replay snapshots for all stages of a pipeline recommendation."""
        rec = (await self.db.execute(
            select(Recommendation).where(Recommendation.id == recommendation_id)
        )).scalar_one_or_none()
        if not rec:
            return []

        now = datetime.now(timezone.utc)
        snapshots = []

        # Selection
        sel = (await self.db.execute(
            select(SelectionRun).where(SelectionRun.recommendation_id == recommendation_id)
        )).scalar_one_or_none()
        if sel:
            snapshots.append(ReplaySnapshot(
                id=gen_uuid(), recommendation_id=recommendation_id, stage="selection",
                snapshot_data={
                    "included_count": len(sel.included_assets or []),
                    "excluded_count": len(sel.excluded_assets or []),
                    "included": sel.included_assets,
                    "rationale": sel.rationale,
                }, captured_at=now,
            ))

        # Allocation
        alloc = (await self.db.execute(
            select(AllocationResult).where(AllocationResult.recommendation_id == recommendation_id)
        )).scalar_one_or_none()
        if alloc:
            snapshots.append(ReplaySnapshot(
                id=gen_uuid(), recommendation_id=recommendation_id, stage="allocation",
                snapshot_data={
                    "method": alloc.method,
                    "positions": len(alloc.weights or {}),
                    "weights": alloc.weights,
                    "rationale": alloc.rationale,
                }, captured_at=now,
            ))

        # Timing
        timing = (await self.db.execute(
            select(TimingResult).where(TimingResult.recommendation_id == recommendation_id)
        )).scalar_one_or_none()
        if timing:
            snapshots.append(ReplaySnapshot(
                id=gen_uuid(), recommendation_id=recommendation_id, stage="timing",
                snapshot_data={
                    "urgency": timing.urgency,
                    "horizon_days": timing.horizon_days,
                    "rationale": timing.rationale,
                }, captured_at=now,
            ))

        # Risk overlay
        overlay = (await self.db.execute(
            select(RiskOverlayResult).where(RiskOverlayResult.recommendation_id == recommendation_id)
        )).scalar_one_or_none()
        if overlay:
            snapshots.append(ReplaySnapshot(
                id=gen_uuid(), recommendation_id=recommendation_id, stage="risk_overlay",
                snapshot_data={
                    "portfolio_risk_score": overlay.portfolio_risk_score,
                    "adjustments": overlay.adjustments,
                    "constraints": overlay.constraints_applied,
                    "rationale": overlay.rationale,
                }, captured_at=now,
            ))

        # Recommendation summary
        snapshots.append(ReplaySnapshot(
            id=gen_uuid(), recommendation_id=recommendation_id, stage="recommendation",
            snapshot_data={
                "status": rec.status,
                "model_confidence": rec.model_confidence,
                "data_confidence": rec.data_confidence,
                "operational_confidence": rec.operational_confidence,
                "rationale": rec.rationale_summary,
                "source_feature_set_id": rec.source_feature_set_id,
                "source_signal_run_ids": rec.source_signal_run_ids,
            }, captured_at=now,
        ))

        for s in snapshots:
            self.db.add(s)
        await self.db.commit()
        return snapshots

    async def ensure_replay_exists(self, recommendation_id: str) -> bool:
        """Check if replay snapshots exist for a recommendation; create if not."""
        count = (await self.db.execute(
            select(func.count()).select_from(ReplaySnapshot)
            .where(ReplaySnapshot.recommendation_id == recommendation_id)
        )).scalar() or 0
        if count > 0:
            return True
        snapshots = await self.create_replay_for_recommendation(recommendation_id)
        return len(snapshots) > 0
