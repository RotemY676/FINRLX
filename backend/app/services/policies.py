"""Policy rules service.

Phase 6F: editable, audited policy constraints.
Publication gates reference these rules for documentation;
hardcoded fallbacks remain active where is_enforced=False.
"""
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy import PolicyRule, PolicyRuleHistory
from app.models.ops import AuditEvent, PolicyBreach
from app.models.base import gen_uuid


DEFAULT_POLICY_RULES = [
    {"key": "position_cap_max", "name": "Max single position", "category": "position_cap",
     "description": "Maximum weight for any single asset", "severity": "block",
     "threshold_value": 0.15, "threshold_unit": "weight", "applies_to": "pipeline",
     "is_enforced": False},
    {"key": "cash_floor", "name": "Cash reserve floor", "category": "cash_floor",
     "description": "Minimum cash allocation", "severity": "warning",
     "threshold_value": 0.05, "threshold_unit": "weight", "applies_to": "pipeline",
     "is_enforced": False},
    {"key": "confidence_model_min", "name": "Min model confidence", "category": "confidence_floor",
     "description": "Minimum model confidence for publication", "severity": "block",
     "threshold_value": 0.25, "threshold_unit": "score", "applies_to": "publication_gate",
     "is_enforced": False},
    {"key": "confidence_data_min", "name": "Min data confidence", "category": "confidence_floor",
     "description": "Minimum data confidence for publication", "severity": "block",
     "threshold_value": 0.50, "threshold_unit": "score", "applies_to": "publication_gate",
     "is_enforced": False},
    {"key": "confidence_operational_min", "name": "Min operational confidence", "category": "confidence_floor",
     "description": "Minimum operational confidence for publication", "severity": "block",
     "threshold_value": 0.50, "threshold_unit": "score", "applies_to": "publication_gate",
     "is_enforced": False},
    {"key": "sector_cap", "name": "Sector concentration cap", "category": "sector_cap",
     "description": "Maximum weight in any single sector", "severity": "warning",
     "threshold_value": 0.30, "threshold_unit": "weight", "applies_to": "pipeline",
     "is_enforced": False},
    {"key": "data_freshness_max_age", "name": "Feature freshness max age", "category": "data_freshness",
     "description": "Maximum age of feature set before warning", "severity": "warning",
     "threshold_value": 24.0, "threshold_unit": "hours", "applies_to": "publication_gate",
     "is_enforced": False},
    {"key": "ml_shadow_only", "name": "ML remains shadow", "category": "model_shadow",
     "description": "ML engines must remain shadow/experimental", "severity": "block",
     "threshold_value": 1.0, "threshold_unit": "boolean", "applies_to": "pipeline",
     "is_enforced": True},
    {"key": "publication_requires_lineage", "name": "Lineage required", "category": "publication_gate",
     "description": "Publication requires pipeline lineage (feature_set + signal_runs)", "severity": "warning",
     "threshold_value": 1.0, "threshold_unit": "boolean", "applies_to": "publication_gate",
     "is_enforced": False},
    {"key": "max_invested", "name": "Max total invested", "category": "exposure_cap",
     "description": "Maximum total invested weight (remainder is cash)", "severity": "warning",
     "threshold_value": 0.95, "threshold_unit": "weight", "applies_to": "pipeline",
     "is_enforced": False},
]


class PolicyService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def ensure_default_policy_rules(self) -> int:
        inserted = 0
        for defn in DEFAULT_POLICY_RULES:
            existing = (await self.db.execute(
                select(PolicyRule.id).where(PolicyRule.key == defn["key"])
            )).scalar()
            if not existing:
                self.db.add(PolicyRule(id=gen_uuid(), **defn))
                inserted += 1
        if inserted:
            await self.db.commit()
        return inserted

    async def get_policy_rules(self) -> list[PolicyRule]:
        return list((await self.db.execute(
            select(PolicyRule).order_by(PolicyRule.category, PolicyRule.key)
        )).scalars().all())

    async def get_policy_rule(self, key: str) -> PolicyRule | None:
        return (await self.db.execute(
            select(PolicyRule).where(PolicyRule.key == key)
        )).scalar_one_or_none()

    async def update_policy_rule(self, key: str, new_value: float, actor: str, reason: str | None) -> PolicyRule | None:
        rule = await self.get_policy_rule(key)
        if not rule:
            return None

        previous = rule.threshold_value
        rule.threshold_value = new_value
        rule.version += 1
        rule.updated_at = datetime.now(timezone.utc)

        self.db.add(PolicyRuleHistory(
            id=gen_uuid(),
            policy_rule_id=rule.id,
            policy_rule_key=rule.key,
            previous_value=previous,
            new_value=new_value,
            actor=actor,
            reason=reason,
        ))
        self.db.add(AuditEvent(
            id=gen_uuid(), actor=actor, action="policy_update",
            object_type="policy_rule", object_id=rule.id,
            details={"key": key, "previous": previous, "new": new_value, "reason": reason},
            occurred_at=datetime.now(timezone.utc),
        ))
        await self.db.commit()
        return rule

    async def get_policy_history(self, key: str) -> list[PolicyRuleHistory]:
        return list((await self.db.execute(
            select(PolicyRuleHistory)
            .where(PolicyRuleHistory.policy_rule_key == key)
            .order_by(PolicyRuleHistory.created_at.desc()).limit(50)
        )).scalars().all())

    async def get_policy_breaches(self) -> list[PolicyBreach]:
        return list((await self.db.execute(
            select(PolicyBreach)
            .where(PolicyBreach.is_active == True)  # noqa: E712
            .order_by(PolicyBreach.severity)
        )).scalars().all())

    async def evaluate_policy_rules(self, context: dict | None = None) -> list[dict]:
        """Evaluate all active policy rules against current state.
        Returns list of rule evaluations with pass/warning/block status."""
        rules = await self.get_policy_rules()
        results = []
        for r in rules:
            if not r.is_active:
                continue
            status = "display_only" if not r.is_enforced else "enforced"
            results.append({
                "key": r.key,
                "name": r.name,
                "category": r.category,
                "severity": r.severity,
                "threshold_value": r.threshold_value,
                "threshold_unit": r.threshold_unit,
                "is_enforced": r.is_enforced,
                "evaluation_status": status,
            })
        return results

    async def get_ops_summary(self) -> dict:
        total = (await self.db.execute(select(func.count()).select_from(PolicyRule))).scalar() or 0
        active = (await self.db.execute(
            select(func.count()).select_from(PolicyRule).where(PolicyRule.is_active == True)  # noqa: E712
        )).scalar() or 0
        enforced = (await self.db.execute(
            select(func.count()).select_from(PolicyRule)
            .where(PolicyRule.is_active == True).where(PolicyRule.is_enforced == True)  # noqa: E712
        )).scalar() or 0
        breaches = (await self.db.execute(
            select(func.count()).select_from(PolicyBreach)
            .where(PolicyBreach.is_active == True)  # noqa: E712
        )).scalar() or 0
        return {
            "total_rules": total,
            "active_rules": active,
            "enforced_rules": enforced,
            "active_breaches": breaches,
        }
