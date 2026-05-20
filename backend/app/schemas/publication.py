"""Publication workflow schemas.

Maps to Doc 14 (Governance, Guardrails, Ops Reliability).
"""
from datetime import datetime

from pydantic import BaseModel, Field


class PublicationGateCheck(BaseModel):
    gate: str
    status: str  # pass, warning, block
    message: str


class PublicationGateResult(BaseModel):
    recommendation_id: str
    overall: str  # pass, warning, block
    gates: list[PublicationGateCheck]
    can_publish: bool


class PublicationActionRequest(BaseModel):
    actor: str = "operator"
    reason: str | None = None


class PublicationTransitionResponse(BaseModel):
    recommendation_id: str
    previous_status: str
    new_status: str
    allowed: bool
    gates: list[PublicationGateCheck] | None = None
    warnings: list[str] = Field(default_factory=list)
    audit_event_id: str | None = None
    message: str


class PublicationStatusResponse(BaseModel):
    total_draft: int = 0
    total_staged: int = 0
    total_approved: int = 0
    total_published: int = 0
    total_deferred: int = 0
    total_suppressed: int = 0
    latest_published_id: str | None = None
    latest_published_at: datetime | None = None


class PublicationHistoryEntry(BaseModel):
    action: str
    actor: str
    timestamp: datetime | None = None
    details: str | None = None
