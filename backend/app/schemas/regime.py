"""Regime and signal posture schemas.

Maps to design handoff: overview.jsx RegimeStrip structure.
"""
from datetime import datetime

from pydantic import BaseModel, Field


class SignalPosture(BaseModel):
    factor: str  # Momentum, Quality, Value, Low-vol
    direction: str  # overweight, underweight, neutral
    sigma: float


class SectorTilt(BaseModel):
    sector: str
    tilt_pct: float  # e.g. +3.2 or -1.6


class RegimeSnapshot(BaseModel):
    """The benchmark's regime under the same rule the dossier uses.

    Zero-fiction note (2026-07-23): this used to return a hardcoded
    "Risk-on · late-cycle" with `regime_confidence=0.78`, alternative-regime
    probabilities, factor sigmas and sector tilts — none of which the system
    has a model to produce. Those fields are now optional and are left empty,
    with `unavailable` naming what is missing and why, rather than filled with
    invented numbers.
    """

    regime_label: str
    regime_detail: str | None = None
    regime_kind: str | None = None
    benchmark: str | None = None
    persistence_days: int | None = None
    last_switch_date: str | None = None
    sessions_observed: int | None = None
    # No model produces these. They stay empty rather than fabricated.
    regime_confidence: float | None = None
    alternatives: list[dict] = Field(default_factory=list)
    signal_posture: list[SignalPosture] = Field(default_factory=list)
    sector_tilts: list[SectorTilt] = Field(default_factory=list)
    unavailable: list[str] = Field(default_factory=list)
    as_of: datetime


class ActivityEvent(BaseModel):
    kind: str  # publish, breach, engine, note, defer, incident, backtest
    actor: str
    description: str
    detail: str | None = None
    when_ago: str  # "12m", "2h"
    timestamp: datetime


class ActivityFeedResponse(BaseModel):
    events: list[ActivityEvent]
    total: int
