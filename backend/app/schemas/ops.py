"""Ops Command Center schemas.

Maps to design handoff: ops.jsx data structures.
"""
from pydantic import BaseModel, Field


class OpsQueueItem(BaseModel):
    id: str | None = None
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
    status: str = "pending"


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


class OpsSystemKpi(BaseModel):
    key: str
    value: str
    sub: str | None = None
    tone: str = "neutral"  # neutral, pos, caution, breach


class OpsMLBlock(BaseModel):
    """Compact ML observability block for ops dashboard."""
    total_models: int = 0
    active_models: int = 0
    shadow_models: int = 0
    latest_validation_status: str | None = None
    promotion_readiness: str | None = None
    warning_count: int = 0
    any_model_influences_live_pipeline: bool = False
    ml_is_shadow_only: bool = True


class OpsPolicyBlock(BaseModel):
    total_rules: int = 0
    active_rules: int = 0
    enforced_rules: int = 0
    active_breaches: int = 0


class OpsIntegrationsBlock(BaseModel):
    total_integrations: int = 0
    healthy: int = 0
    degraded: int = 0
    placeholder: int = 0
    real_providers: int = 0


class OpsUniverseBlock(BaseModel):
    total_universes: int = 0
    total_assets: int = 0
    default_universe_name: str | None = None
    default_readiness: str | None = None


class OpsCommandCenterResponse(BaseModel):
    queue: list[OpsQueueItem]
    feeds: list[OpsFeed]
    engines: list[OpsEngine]
    breaches: list[OpsBreach]
    incidents: list[OpsIncident]
    audit: list[OpsAuditEntry]
    system_kpis: list[OpsSystemKpi] = Field(default_factory=list)
    ml_ops: OpsMLBlock | None = None
    policy: OpsPolicyBlock | None = None
    integrations_summary: OpsIntegrationsBlock | None = None
    universe: OpsUniverseBlock | None = None


class QueueActionResponse(BaseModel):
    id: str
    new_status: str
    message: str


class WorkspaceCounts(BaseModel):
    overview: int = 0
    decisions: int = 0
    risk: int = 0
    ops: int = 0
