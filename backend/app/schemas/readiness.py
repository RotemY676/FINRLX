"""Unified readiness manifest contracts (US-P0-08).

Aggregates per-domain readiness (market-data freshness, FX freshness, provider
configuration) into one operator view with an explicit overall verdict and the
affected scope for anything not ready. Fail-closed: a component that cannot be
evaluated is reported ``unavailable`` (never silently ``ready``).
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

# Ordered worst-last so overall status is a simple max.
READINESS_STATUSES = ("ready", "degraded", "unavailable")


class ReadinessComponent(BaseModel):
    name: str
    status: str  # ready | degraded | unavailable
    detail: str | None = None
    affected: list[str] = Field(default_factory=list)
    metrics: dict[str, int] = Field(default_factory=dict)


class ReadinessReport(BaseModel):
    generated_at: datetime
    overall: str
    ready: bool
    components: list[ReadinessComponent] = Field(default_factory=list)
