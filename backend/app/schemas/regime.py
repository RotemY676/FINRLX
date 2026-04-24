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
    regime_label: str  # "Risk-on · late-cycle"
    regime_confidence: float
    persistence_days: int
    last_switch_date: str
    alternatives: list[dict] = Field(default_factory=list)  # [{label, prob}]
    signal_posture: list[SignalPosture] = Field(default_factory=list)
    sector_tilts: list[SectorTilt] = Field(default_factory=list)
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
