"""Publication workflow service.

Phase 4E: governed state machine for recommendation publication.
Doc 14: Governance, Guardrails, Ops Reliability Specification.

State machine:
  draft -> staged -> approved -> published
  draft -> suppressed
  staged -> deferred | suppressed
  approved -> deferred
  published -> superseded
"""
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import gen_uuid
from app.models.feature import FeatureSet
from app.models.ops import AuditEvent, Incident, PolicyBreach
from app.models.recommendation import Recommendation, RecommendationWeight

# ── State machine ────────────────────────────────────────────────────

ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["staged", "suppressed"],
    "staged": ["approved", "deferred", "suppressed"],
    "approved": ["published", "published_with_warning", "deferred"],
    "published": ["superseded"],
    "published_with_warning": ["superseded"],
    "deferred": ["staged"],  # can restage after deferral
    "suppressed": [],
    "superseded": [],
}

MAX_POSITION_WEIGHT = 0.15
MIN_MODEL_CONFIDENCE = 0.25
MIN_DATA_CONFIDENCE = 0.50
MIN_OPERATIONAL_CONFIDENCE = 0.50


class PublicationService:
    """Manages the publication lifecycle of recommendations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Gate evaluation ───────────────────────────────────────────────

    async def evaluate_gates(self, recommendation_id: str) -> dict:
        """Evaluate all publication gates for a recommendation."""
        rec = (await self.db.execute(
            select(Recommendation).where(Recommendation.id == recommendation_id)
        )).scalar_one_or_none()

        if not rec:
            return {
                "recommendation_id": recommendation_id,
                "overall": "block",
                "gates": [{"gate": "exists", "status": "block", "message": "Recommendation not found"}],
                "can_publish": False,
            }

        gates = []

        # 1. Pipeline lineage
        if rec.source_feature_set_id:
            gates.append({"gate": "lineage", "status": "pass", "message": "Pipeline lineage present"})
        else:
            gates.append({"gate": "lineage", "status": "warning", "message": "No pipeline lineage (may be seeded)"})

        # 2. Signal coverage
        if rec.source_signal_run_ids and len(rec.source_signal_run_ids) > 0:
            gates.append({"gate": "signals", "status": "pass", "message": f"{len(rec.source_signal_run_ids)} signal runs"})
        else:
            gates.append({"gate": "signals", "status": "warning", "message": "No signal run lineage"})

        # 3. Weights exist
        wt_count = (await self.db.execute(
            select(func.count()).select_from(RecommendationWeight)
            .where(RecommendationWeight.recommendation_id == rec.id)
        )).scalar() or 0
        if wt_count > 0:
            gates.append({"gate": "weights", "status": "pass", "message": f"{wt_count} positions"})
        else:
            gates.append({"gate": "weights", "status": "block", "message": "No weights — cannot publish empty recommendation"})

        # 4. Position cap
        max_wt = (await self.db.execute(
            select(func.max(RecommendationWeight.target_weight))
            .where(RecommendationWeight.recommendation_id == rec.id)
        )).scalar() or 0
        if max_wt <= MAX_POSITION_WEIGHT + 0.005:
            gates.append({"gate": "position_cap", "status": "pass", "message": f"Max position {max_wt:.1%}"})
        else:
            gates.append({"gate": "position_cap", "status": "block", "message": f"Max position {max_wt:.1%} exceeds {MAX_POSITION_WEIGHT:.0%} cap"})

        # 5. Confidence thresholds
        if (rec.model_confidence or 0) >= MIN_MODEL_CONFIDENCE:
            gates.append({"gate": "model_confidence", "status": "pass", "message": f"Model confidence {rec.model_confidence:.2f}"})
        else:
            gates.append({"gate": "model_confidence", "status": "block", "message": f"Model confidence {rec.model_confidence or 0:.2f} < {MIN_MODEL_CONFIDENCE}"})

        if (rec.data_confidence or 0) >= MIN_DATA_CONFIDENCE:
            gates.append({"gate": "data_confidence", "status": "pass", "message": f"Data confidence {rec.data_confidence:.2f}"})
        else:
            gates.append({"gate": "data_confidence", "status": "block", "message": f"Data confidence {rec.data_confidence or 0:.2f} < {MIN_DATA_CONFIDENCE}"})

        if (rec.operational_confidence or 0) >= MIN_OPERATIONAL_CONFIDENCE:
            gates.append({"gate": "operational_confidence", "status": "pass", "message": f"Operational confidence {rec.operational_confidence:.2f}"})
        else:
            gates.append({"gate": "operational_confidence", "status": "block", "message": f"Operational confidence {rec.operational_confidence or 0:.2f} < {MIN_OPERATIONAL_CONFIDENCE}"})

        # 6. Feature freshness
        if rec.source_feature_set_id:
            fs = (await self.db.execute(
                select(FeatureSet).where(FeatureSet.id == rec.source_feature_set_id)
            )).scalar_one_or_none()
            if fs and fs.freshness_status in ("healthy", "degraded"):
                gates.append({"gate": "feature_freshness", "status": "pass", "message": f"Feature set {fs.freshness_status}"})
            elif fs:
                gates.append({"gate": "feature_freshness", "status": "warning", "message": f"Feature set {fs.freshness_status}"})
            else:
                gates.append({"gate": "feature_freshness", "status": "warning", "message": "Feature set not found"})

        # 7. No critical incidents
        critical_incidents = (await self.db.execute(
            select(func.count()).select_from(Incident)
            .where(Incident.status != "resolved")
            .where(Incident.severity <= 2)
        )).scalar() or 0
        if critical_incidents == 0:
            gates.append({"gate": "incidents", "status": "pass", "message": "No critical incidents"})
        else:
            gates.append({"gate": "incidents", "status": "block", "message": f"Publication blocked: {critical_incidents} critical incident(s) open"})

        # 8. No blocking policy breaches
        blocking_breaches = (await self.db.execute(
            select(func.count()).select_from(PolicyBreach)
            .where(PolicyBreach.is_active == True)  # noqa: E712
            .where(PolicyBreach.severity == "breach")
        )).scalar() or 0
        if blocking_breaches == 0:
            gates.append({"gate": "policy_breaches", "status": "pass", "message": "No blocking breaches"})
        else:
            gates.append({"gate": "policy_breaches", "status": "block", "message": f"Publication blocked: {blocking_breaches} active policy breach(es)"})

        # Compute overall
        has_block = any(g["status"] == "block" for g in gates)
        has_warning = any(g["status"] == "warning" for g in gates)
        overall = "block" if has_block else "warning" if has_warning else "pass"

        return {
            "recommendation_id": recommendation_id,
            "overall": overall,
            "gates": gates,
            "can_publish": not has_block,
        }

    # ── Transitions ───────────────────────────────────────────────────

    async def _transition(self, recommendation_id: str, target_status: str, actor: str, reason: str | None) -> dict:
        """Execute a state transition with validation and audit."""
        rec = (await self.db.execute(
            select(Recommendation).where(Recommendation.id == recommendation_id)
        )).scalar_one_or_none()

        if not rec:
            return {
                "recommendation_id": recommendation_id,
                "previous_status": "", "new_status": "",
                "allowed": False, "gates": None, "warnings": [],
                "audit_event_id": None,
                "message": "Recommendation not found",
            }

        current = rec.status
        allowed = ALLOWED_TRANSITIONS.get(current, [])

        if target_status not in allowed:
            return {
                "recommendation_id": recommendation_id,
                "previous_status": current, "new_status": current,
                "allowed": False, "gates": None,
                "warnings": [f"Transition {current} -> {target_status} is not allowed"],
                "audit_event_id": None,
                "message": f"Cannot transition from {current} to {target_status}. Allowed: {', '.join(allowed) or 'none'}",
            }

        # For publish transitions, check gates
        gate_result = None
        if target_status in ("published", "published_with_warning"):
            gate_result = await self.evaluate_gates(recommendation_id)
            if not gate_result["can_publish"]:
                blocked_gates = [g for g in gate_result["gates"] if g["status"] == "block"]
                return {
                    "recommendation_id": recommendation_id,
                    "previous_status": current, "new_status": current,
                    "allowed": False,
                    "gates": gate_result["gates"],
                    "warnings": [g["message"] for g in blocked_gates],
                    "audit_event_id": None,
                    "message": f"Publication blocked: {blocked_gates[0]['message'] if blocked_gates else 'gate failure'}",
                }
            # If warnings exist but no blocks, publish with warning
            if gate_result["overall"] == "warning":
                target_status = "published_with_warning"

        # For defer/suppress, require reason
        if target_status in ("deferred", "suppressed") and not reason:
            return {
                "recommendation_id": recommendation_id,
                "previous_status": current, "new_status": current,
                "allowed": False, "gates": None,
                "warnings": [f"{target_status} requires a reason"],
                "audit_event_id": None,
                "message": f"Reason is required for {target_status}",
            }

        # Execute transition
        rec.status = target_status
        if target_status in ("published", "published_with_warning"):
            rec.published_at = datetime.now(UTC)
            # Supersede any previously published recommendations
            prev_published = (await self.db.execute(
                select(Recommendation)
                .where(Recommendation.id != rec.id)
                .where(Recommendation.status.in_(["published", "published_with_warning"]))
            )).scalars().all()
            for prev in prev_published:
                prev.status = "superseded"

        # Audit
        audit = AuditEvent(
            id=gen_uuid(),
            actor=actor,
            action=f"publication_{target_status}",
            object_type="recommendation",
            object_id=recommendation_id,
            details={
                "previous_status": current,
                "new_status": target_status,
                "reason": reason,
                "gate_result": gate_result["overall"] if gate_result else None,
            },
            occurred_at=datetime.now(UTC),
        )
        self.db.add(audit)
        await self.db.commit()

        return {
            "recommendation_id": recommendation_id,
            "previous_status": current,
            "new_status": target_status,
            "allowed": True,
            "gates": gate_result["gates"] if gate_result else None,
            "warnings": [],
            "audit_event_id": audit.id,
            "message": f"Recommendation {target_status} successfully",
        }

    async def stage(self, recommendation_id: str, actor: str, reason: str | None = None) -> dict:
        return await self._transition(recommendation_id, "staged", actor, reason)

    async def approve(self, recommendation_id: str, actor: str, reason: str | None = None) -> dict:
        return await self._transition(recommendation_id, "approved", actor, reason)

    async def publish(self, recommendation_id: str, actor: str, reason: str | None = None) -> dict:
        return await self._transition(recommendation_id, "published", actor, reason)

    async def defer(self, recommendation_id: str, actor: str, reason: str) -> dict:
        return await self._transition(recommendation_id, "deferred", actor, reason)

    async def suppress(self, recommendation_id: str, actor: str, reason: str) -> dict:
        return await self._transition(recommendation_id, "suppressed", actor, reason)

    # ── Status ────────────────────────────────────────────────────────

    async def get_status(self) -> dict:
        counts = {}
        for status in ["draft", "staged", "approved", "published", "published_with_warning", "deferred", "suppressed"]:
            c = (await self.db.execute(
                select(func.count()).select_from(Recommendation).where(Recommendation.status == status)
            )).scalar() or 0
            counts[status] = c

        latest_pub = (await self.db.execute(
            select(Recommendation)
            .where(Recommendation.status.in_(["published", "published_with_warning"]))
            .order_by(Recommendation.published_at.desc()).limit(1)
        )).scalar_one_or_none()

        return {
            "total_draft": counts.get("draft", 0),
            "total_staged": counts.get("staged", 0),
            "total_approved": counts.get("approved", 0),
            "total_published": counts.get("published", 0) + counts.get("published_with_warning", 0),
            "total_deferred": counts.get("deferred", 0),
            "total_suppressed": counts.get("suppressed", 0),
            "latest_published_id": latest_pub.id if latest_pub else None,
            "latest_published_at": latest_pub.published_at if latest_pub else None,
        }

    async def get_history(self, recommendation_id: str) -> list[dict]:
        events = (await self.db.execute(
            select(AuditEvent)
            .where(AuditEvent.object_type == "recommendation")
            .where(AuditEvent.object_id == recommendation_id)
            .order_by(AuditEvent.occurred_at.desc())
        )).scalars().all()
        return [
            {"action": e.action, "actor": e.actor, "timestamp": e.occurred_at,
             "details": (e.details or {}).get("reason") or (e.details or {}).get("description")}
            for e in events
        ]

    async def get_queue(self) -> list[dict]:
        """Return recommendations in active workflow states (staged, approved, deferred, suppressed)."""
        recs = (await self.db.execute(
            select(Recommendation)
            .where(Recommendation.status.in_(["staged", "approved", "deferred", "suppressed"]))
            .order_by(Recommendation.updated_at.desc())
        )).scalars().all()

        result = []
        for r in recs:
            wt_count = (await self.db.execute(
                select(func.count()).select_from(RecommendationWeight)
                .where(RecommendationWeight.recommendation_id == r.id)
            )).scalar() or 0
            warning_list = r.warnings if isinstance(r.warnings, list) else []
            result.append({
                "recommendation_id": r.id,
                "status": r.status,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
                "model_confidence": r.model_confidence,
                "data_confidence": r.data_confidence,
                "operational_confidence": r.operational_confidence,
                "warning_count": len(warning_list),
                "weight_count": wt_count,
                "source_feature_set_id": r.source_feature_set_id,
                "source_signal_run_ids": r.source_signal_run_ids,
            })
        return result
