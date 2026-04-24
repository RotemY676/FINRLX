"""Ops Command Center schemas.

Maps to design handoff: ops.jsx data structures.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class OpsQueueItem(BaseModel):
    recommendation_id: str
    ticker: str
    stance: str
    version: str
    submitted_ago: str
    submitter: str
    weight: str
    confidence: float
    flags: list[str] = Field(default_factory=list)
    priority: str  # high, mid, low


class OpsFeed(BaseModel):
    name: str
    status: str  # ok, degraded, stale
    lag: str
    coverage: str
    slo: float


class OpsEngine(BaseModel):
    name: str
    latency: str
    drift: float
    last_run: str
    status: str  # ok, warn, degraded


class OpsBreach(BaseModel):
    kind: str
    label: str
    utilization: float
    trend: str
    severity: str  # high, mid, breach
    related: str


class OpsIncident(BaseModel):
    id: str
    title: str
    started: str
    severity: str
    owner: str
    status: str
    affected_recs: int
    note: str


class OpsAuditEntry(BaseModel):
    when: str
    actor: str
    action: str
    target: str
    scope: str
    ok: bool


class OpsCommandCenterResponse(BaseModel):
    queue: list[OpsQueueItem]
    feeds: list[OpsFeed]
    engines: list[OpsEngine]
    breaches: list[OpsBreach]
    incidents: list[OpsIncident]
    audit: list[OpsAuditEntry]
