"""Canonical decision packet contracts for evidence-before-action surfaces.

The packet is deliberately stricter than the legacy recommendation response.
It carries the market-data truth, forecast distribution, validation evidence,
risk frame, lineage, and an explicit capability gate in one versioned object.

Backtests remain historical evidence. A packet may become eligible for human
review only after the truth gate passes; this contract never authorizes broker
execution or promises future returns.
"""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ContractModel(BaseModel):
    """Strict base class so unrecognised evidence fields cannot be ignored."""

    model_config = ConfigDict(extra="forbid")


class MarketDataStatus(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class CalibrationStatus(str, Enum):
    VALIDATED = "validated"
    PARTIAL = "partial"
    UNVALIDATED = "unvalidated"


class ProspectiveMode(str, Enum):
    NONE = "none"
    SHADOW = "shadow"
    PAPER = "paper"


class DecisionIntent(str, Enum):
    OBSERVE = "observe"
    RESEARCH = "research"
    CANDIDATE_ENTRY = "candidate_entry"
    HOLD = "hold"
    CANDIDATE_REDUCE = "candidate_reduce"
    EXIT = "exit"
    AVOID = "avoid"


class GateCapability(str, Enum):
    DECISION = "decision"
    TARGET = "target"
    ALERT = "alert"


class GateSeverity(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    BLOCK = "block"


class PacketOutcome(str, Enum):
    BLOCKED = "blocked"
    RESEARCH_ONLY = "research_only"
    READY_FOR_REVIEW = "ready_for_review"


class DecisionConfidence(ContractModel):
    model: float = Field(ge=0, le=1)
    data: float = Field(ge=0, le=1)
    operational: float = Field(ge=0, le=1)


class DataTruth(ContractModel):
    data_as_of: datetime
    expected_latest_session: date
    latest_market_session: date | None = None
    status: MarketDataStatus
    lag_trading_days: int | None = Field(default=None, ge=0)
    source_chain: list[str] = Field(default_factory=list)
    selected_source: str | None = None
    fallback_used: bool = False
    is_demo: bool = False
    is_synthetic: bool = False
    quality_warnings: list[str] = Field(default_factory=list)

    @field_validator("data_as_of")
    @classmethod
    def data_as_of_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("data_as_of must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_source_and_session_truth(self) -> DataTruth:
        if self.selected_source and self.selected_source not in self.source_chain:
            raise ValueError("selected_source must appear in source_chain")
        if (
            self.latest_market_session is not None
            and self.latest_market_session > self.expected_latest_session
        ):
            raise ValueError("latest_market_session cannot be after expected_latest_session")
        if self.status == MarketDataStatus.FRESH:
            if self.latest_market_session is None:
                raise ValueError("fresh market data requires latest_market_session")
            if self.selected_source is None:
                raise ValueError("fresh market data requires selected_source")
        return self


class ForecastDistribution(ContractModel):
    horizon_trading_days: int = Field(gt=0, le=252)
    currency: str = Field(min_length=3, max_length=3)
    p10: float = Field(gt=0)
    p50: float = Field(gt=0)
    p90: float = Field(gt=0)
    generated_at: datetime
    model_version: str = Field(min_length=1)
    calibration_status: CalibrationStatus
    calibration_window: str | None = None
    limitations: list[str] = Field(default_factory=list)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.upper()
        if not normalized.isalpha():
            raise ValueError("currency must be a three-letter code")
        return normalized

    @field_validator("generated_at")
    @classmethod
    def generated_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_quantile_order(self) -> ForecastDistribution:
        if not self.p10 <= self.p50 <= self.p90:
            raise ValueError("forecast quantiles must satisfy p10 <= p50 <= p90")
        return self


class BacktestEvidence(ContractModel):
    backtest_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    source_type: str = "unknown"
    is_demo: bool = True
    lineage_available: bool = False
    out_of_sample: bool = False
    cost_bps: float | None = Field(default=None, ge=0)
    slippage_bps: float | None = Field(default=None, ge=0)
    observations: int = Field(default=0, ge=0)
    start_date: date | None = None
    end_date: date | None = None
    promotion_gate_passed: bool = False
    promotion_gate_version: str | None = None
    metrics: dict[str, float | int | None] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_window(self) -> BacktestEvidence:
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("backtest end_date must not precede start_date")
        return self


class ValidationEvidence(ContractModel):
    backtest: BacktestEvidence | None = None
    prospective_mode: ProspectiveMode = ProspectiveMode.NONE
    prospective_days: int = Field(default=0, ge=0)
    paper_portfolio_id: str | None = None
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_prospective_identity(self) -> ValidationEvidence:
        if self.prospective_mode == ProspectiveMode.NONE and self.prospective_days:
            raise ValueError("prospective_days requires shadow or paper mode")
        if self.prospective_mode == ProspectiveMode.PAPER and not self.paper_portfolio_id:
            raise ValueError("paper mode requires paper_portfolio_id")
        return self


class RiskFrame(ContractModel):
    max_position_weight: float | None = Field(default=None, gt=0, le=1)
    invalidation_price: float | None = Field(default=None, gt=0)
    invalidation_reason: str | None = None
    risk_flags: list[str] = Field(default_factory=list)


class DecisionLineage(ContractModel):
    data_snapshot_id: str | None = None
    feature_snapshot_id: str | None = None
    signal_run_id: str | None = None
    model_version: str | None = None
    policy_version_id: str | None = None
    code_version: str | None = None


class GateCheck(ContractModel):
    code: str = Field(min_length=1)
    capability: GateCapability
    severity: GateSeverity
    message: str = Field(min_length=1)


class TruthGate(ContractModel):
    policy_version: str = Field(min_length=1)
    outcome: PacketOutcome
    can_surface_decision: bool
    can_show_target: bool
    can_enable_alert: bool
    checks: list[GateCheck]

    @model_validator(mode="after")
    def validate_capability_hierarchy(self) -> TruthGate:
        if self.can_show_target and not self.can_surface_decision:
            raise ValueError("target capability requires decision capability")
        if self.can_enable_alert and not self.can_show_target:
            raise ValueError("alert capability requires target capability")

        capability_state = {
            GateCapability.DECISION: self.can_surface_decision,
            GateCapability.TARGET: self.can_show_target,
            GateCapability.ALERT: self.can_enable_alert,
        }
        for check in self.checks:
            if check.severity == GateSeverity.BLOCK and capability_state[check.capability]:
                raise ValueError(
                    f"{check.capability.value} cannot be enabled while {check.code} blocks it"
                )

        expected_outcome = (
            PacketOutcome.BLOCKED
            if not self.can_surface_decision
            else PacketOutcome.READY_FOR_REVIEW
            if self.can_enable_alert
            else PacketOutcome.RESEARCH_ONLY
        )
        if self.outcome != expected_outcome:
            raise ValueError("outcome does not match the enabled capabilities")
        return self


class DecisionPacket(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    packet_id: str = Field(min_length=1)
    recommendation_id: str = Field(min_length=1)
    ticker: str = Field(pattern=r"^[A-Z][A-Z0-9.\-]{0,9}$")
    created_at: datetime
    intent: DecisionIntent
    rationale: str
    confidence: DecisionConfidence
    data: DataTruth
    forecast: ForecastDistribution | None = None
    evidence: ValidationEvidence
    risk: RiskFrame | None = None
    lineage: DecisionLineage
    gate: TruthGate
    warnings: list[str] = Field(default_factory=list)

    @field_validator("ticker", mode="before")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("created_at")
    @classmethod
    def created_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        return value


class DecisionTruthPolicy(ContractModel):
    version: str = "decision-truth-p0.1"
    max_fresh_lag_trading_days: int = Field(default=1, ge=0)
    min_model_confidence: float = Field(default=0.50, ge=0, le=1)
    min_data_confidence: float = Field(default=0.70, ge=0, le=1)
    min_operational_confidence: float = Field(default=0.70, ge=0, le=1)
    min_backtest_observations: int = Field(default=60, ge=1)
    min_prospective_days: int = Field(default=20, ge=1)
    require_out_of_sample: bool = True
    require_costs_and_slippage: bool = True
    require_promotion_gate: bool = True


class DecisionPacketBundle(BaseModel):
    """API envelope for the packets projected from a single recommendation.

    Not a strict ``ContractModel`` — this is a response wrapper, not an evidence
    contract. The per-packet ``gate.outcome`` remains the authoritative,
    explicit blocked / research_only / ready_for_review state for each ticker.
    """

    recommendation_id: str
    policy_version: str
    count: int
    outcomes: dict[str, int] = Field(default_factory=dict)
    packets: list[DecisionPacket] = Field(default_factory=list)

