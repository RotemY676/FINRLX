"""Policy rules endpoints.

GET   /api/v1/policies/rules
GET   /api/v1/policies/rules/{key}
PATCH /api/v1/policies/rules/{key}
GET   /api/v1/policies/rules/{key}/history
GET   /api/v1/policies/breaches
POST  /api/v1/policies/evaluate
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import make_meta
from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.services.policies import PolicyService

router = APIRouter()


class PolicyRuleUpdateRequest(BaseModel):
    threshold_value: float
    actor: str
    reason: str | None = None


def _rule_dict(r) -> dict:
    return {
        "id": r.id, "key": r.key, "name": r.name, "category": r.category,
        "description": r.description, "severity": r.severity,
        "threshold_value": r.threshold_value, "threshold_unit": r.threshold_unit,
        "applies_to": r.applies_to, "is_active": r.is_active,
        "is_enforced": r.is_enforced, "version": r.version,
    }


@router.get("/policies/rules", response_model=ApiResponse[list[dict]])
async def list_policy_rules(db: AsyncSession = Depends(get_db)):
    svc = PolicyService(db)
    await svc.ensure_default_policy_rules()
    rules = await svc.get_policy_rules()
    return ApiResponse(meta=make_meta(), data=[_rule_dict(r) for r in rules])


@router.get("/policies/rules/{key}", response_model=ApiResponse[dict])
async def get_policy_rule(key: str, db: AsyncSession = Depends(get_db)):
    svc = PolicyService(db)
    rule = await svc.get_policy_rule(key)
    if not rule:
        raise HTTPException(status_code=404, detail="Policy rule not found")
    return ApiResponse(meta=make_meta(), data=_rule_dict(rule))


@router.patch("/policies/rules/{key}", response_model=ApiResponse[dict])
async def update_policy_rule(key: str, body: PolicyRuleUpdateRequest, db: AsyncSession = Depends(get_db)):
    svc = PolicyService(db)
    rule = await svc.update_policy_rule(key, body.threshold_value, body.actor, body.reason)
    if not rule:
        raise HTTPException(status_code=404, detail="Policy rule not found")
    return ApiResponse(meta=make_meta(), data=_rule_dict(rule))


@router.get("/policies/rules/{key}/history", response_model=ApiResponse[list[dict]])
async def get_policy_history(key: str, db: AsyncSession = Depends(get_db)):
    svc = PolicyService(db)
    history = await svc.get_policy_history(key)
    return ApiResponse(meta=make_meta(), data=[
        {"id": h.id, "policy_rule_key": h.policy_rule_key,
         "previous_value": h.previous_value, "new_value": h.new_value,
         "actor": h.actor, "reason": h.reason,
         "created_at": h.created_at.isoformat() if h.created_at else None}
        for h in history
    ])


@router.get("/policies/breaches", response_model=ApiResponse[list[dict]])
async def get_policy_breaches(db: AsyncSession = Depends(get_db)):
    svc = PolicyService(db)
    breaches = await svc.get_policy_breaches()
    return ApiResponse(meta=make_meta(), data=[
        {"kind": b.kind, "label": b.label, "utilization": b.utilization,
         "trend": b.trend, "severity": b.severity, "related": b.related,
         "is_active": b.is_active}
        for b in breaches
    ])


@router.post("/policies/evaluate", response_model=ApiResponse[list[dict]])
async def evaluate_policies(db: AsyncSession = Depends(get_db)):
    svc = PolicyService(db)
    await svc.ensure_default_policy_rules()
    results = await svc.evaluate_policy_rules()
    return ApiResponse(meta=make_meta(), data=results)
