"""Truth-gate evaluation and canonical DecisionPacket construction."""
from __future__ import annotations

from datetime import datetime

from app.schemas.decision_packet import (
    CalibrationStatus,
    DataTruth,
    DecisionConfidence,
    DecisionIntent,
    DecisionLineage,
    DecisionPacket,
    DecisionTruthPolicy,
    ForecastDistribution,
    GateCapability,
    GateCheck,
    GateSeverity,
    MarketDataStatus,
    PacketOutcome,
    ProspectiveMode,
    RiskFrame,
    TruthGate,
    ValidationEvidence,
)


def evaluate_truth_gate(
    *,
    data: DataTruth,
    confidence: DecisionConfidence,
    forecast: ForecastDistribution | None,
    evidence: ValidationEvidence,
    risk: RiskFrame | None,
    lineage: DecisionLineage,
    policy: DecisionTruthPolicy | None = None,
) -> TruthGate:
    """Evaluate which product capabilities may be exposed.

    Capability scopes are independent and hierarchical: a clean data/lineage
    foundation may allow a research decision while an unvalidated forecast
    hides the target, and insufficient historical/prospective evidence keeps
    alerts disabled. No missing fact silently defaults to a pass.
    """

    policy = policy or DecisionTruthPolicy()
    checks: list[GateCheck] = []

    def add(
        code: str,
        capability: GateCapability,
        severity: GateSeverity,
        message: str,
    ) -> None:
        checks.append(
            GateCheck(
                code=code,
                capability=capability,
                severity=severity,
                message=message,
            )
        )

    if data.status != MarketDataStatus.FRESH:
        add(
            "DATA_NOT_FRESH",
            GateCapability.DECISION,
            GateSeverity.BLOCK,
            f"market data status is {data.status.value}",
        )
    elif data.lag_trading_days is None:
        add(
            "DATA_LAG_UNKNOWN",
            GateCapability.DECISION,
            GateSeverity.BLOCK,
            "freshness lag is not known",
        )
    elif data.lag_trading_days > policy.max_fresh_lag_trading_days:
        add(
            "DATA_LAG_EXCEEDS_POLICY",
            GateCapability.DECISION,
            GateSeverity.BLOCK,
            "market data lag exceeds the decision policy",
        )
    else:
        add("DATA_FRESH", GateCapability.DECISION, GateSeverity.PASS, "market data is fresh")

    if data.is_demo:
        add(
            "DEMO_DATA",
            GateCapability.DECISION,
            GateSeverity.BLOCK,
            "demo data cannot support a surfaced decision",
        )
    if data.is_synthetic:
        add(
            "SYNTHETIC_DATA",
            GateCapability.DECISION,
            GateSeverity.BLOCK,
            "synthetic data cannot be presented as market evidence",
        )
    if not data.source_chain or not data.selected_source:
        add(
            "SOURCE_PROVENANCE_MISSING",
            GateCapability.DECISION,
            GateSeverity.BLOCK,
            "selected market-data source and source chain are required",
        )
    if data.fallback_used:
        add(
            "FALLBACK_DISCLOSED",
            GateCapability.DECISION,
            GateSeverity.WARNING,
            f"fallback source {data.selected_source} supplied the market data",
        )

    confidence_rows = (
        ("MODEL_CONFIDENCE_LOW", confidence.model, policy.min_model_confidence, "model"),
        ("DATA_CONFIDENCE_LOW", confidence.data, policy.min_data_confidence, "data"),
        (
            "OPERATIONAL_CONFIDENCE_LOW",
            confidence.operational,
            policy.min_operational_confidence,
            "operational",
        ),
    )
    for code, value, minimum, label in confidence_rows:
        if value < minimum:
            add(
                code,
                GateCapability.DECISION,
                GateSeverity.BLOCK,
                f"{label} confidence {value:.2f} is below policy minimum {minimum:.2f}",
            )

    required_lineage = {
        "data_snapshot_id": lineage.data_snapshot_id,
        "feature_snapshot_id": lineage.feature_snapshot_id,
        "signal_run_id": lineage.signal_run_id,
        "model_version": lineage.model_version,
        "code_version": lineage.code_version,
    }
    missing_lineage = [name for name, value in required_lineage.items() if not value]
    if missing_lineage:
        add(
            "LINEAGE_INCOMPLETE",
            GateCapability.DECISION,
            GateSeverity.BLOCK,
            "missing lineage: " + ", ".join(missing_lineage),
        )
    else:
        add(
            "LINEAGE_COMPLETE",
            GateCapability.DECISION,
            GateSeverity.PASS,
            "data, feature, signal, model, and code lineage is present",
        )

    if forecast is None:
        add(
            "FORECAST_MISSING",
            GateCapability.TARGET,
            GateSeverity.BLOCK,
            "target distribution is unavailable",
        )
    else:
        if forecast.calibration_status != CalibrationStatus.VALIDATED:
            add(
                "FORECAST_NOT_VALIDATED",
                GateCapability.TARGET,
                GateSeverity.BLOCK,
                "target distribution has not passed calibration validation",
            )
        elif forecast.generated_at < data.data_as_of:
            add(
                "FORECAST_PREDATES_DATA",
                GateCapability.TARGET,
                GateSeverity.BLOCK,
                "target distribution predates its market-data snapshot",
            )
        elif lineage.model_version and forecast.model_version != lineage.model_version:
            add(
                "FORECAST_MODEL_MISMATCH",
                GateCapability.TARGET,
                GateSeverity.BLOCK,
                "forecast model version does not match decision lineage",
            )
        else:
            add(
                "FORECAST_VALIDATED",
                GateCapability.TARGET,
                GateSeverity.PASS,
                "calibrated target distribution is available",
            )

    backtest = evidence.backtest
    if backtest is None:
        add(
            "BACKTEST_MISSING",
            GateCapability.ALERT,
            GateSeverity.BLOCK,
            "alert eligibility requires a linked backtest",
        )
    else:
        if backtest.status != "completed":
            add(
                "BACKTEST_NOT_COMPLETED",
                GateCapability.ALERT,
                GateSeverity.BLOCK,
                "linked backtest is not completed",
            )
        if backtest.is_demo:
            add(
                "BACKTEST_IS_DEMO",
                GateCapability.ALERT,
                GateSeverity.BLOCK,
                "demo backtests cannot enable alerts",
            )
        if not backtest.lineage_available:
            add(
                "BACKTEST_LINEAGE_MISSING",
                GateCapability.ALERT,
                GateSeverity.BLOCK,
                "backtest lineage is unavailable",
            )
        if policy.require_out_of_sample and not backtest.out_of_sample:
            add(
                "BACKTEST_NOT_OUT_OF_SAMPLE",
                GateCapability.ALERT,
                GateSeverity.BLOCK,
                "out-of-sample validation is required",
            )
        if policy.require_costs_and_slippage and (
            backtest.cost_bps is None or backtest.slippage_bps is None
        ):
            add(
                "BACKTEST_COST_MODEL_MISSING",
                GateCapability.ALERT,
                GateSeverity.BLOCK,
                "cost and slippage assumptions are required",
            )
        if backtest.observations < policy.min_backtest_observations:
            add(
                "BACKTEST_SAMPLE_TOO_SMALL",
                GateCapability.ALERT,
                GateSeverity.BLOCK,
                "backtest observation count is below policy minimum",
            )
        if policy.require_promotion_gate and not backtest.promotion_gate_passed:
            add(
                "PROMOTION_GATE_NOT_PASSED",
                GateCapability.ALERT,
                GateSeverity.BLOCK,
                "backtest has not passed the versioned promotion gate",
            )

    if evidence.prospective_mode == ProspectiveMode.NONE:
        add(
            "PROSPECTIVE_VALIDATION_MISSING",
            GateCapability.ALERT,
            GateSeverity.BLOCK,
            "shadow or paper validation is required before enabling alerts",
        )
    elif evidence.prospective_days < policy.min_prospective_days:
        add(
            "PROSPECTIVE_WINDOW_TOO_SHORT",
            GateCapability.ALERT,
            GateSeverity.BLOCK,
            "prospective validation window is below policy minimum",
        )

    if risk is None:
        add(
            "RISK_FRAME_MISSING",
            GateCapability.ALERT,
            GateSeverity.BLOCK,
            "alert eligibility requires an explicit risk frame",
        )
    else:
        if risk.max_position_weight is None:
            add(
                "POSITION_LIMIT_MISSING",
                GateCapability.ALERT,
                GateSeverity.BLOCK,
                "maximum position weight is not defined",
            )
        if not risk.invalidation_reason:
            add(
                "INVALIDATION_RULE_MISSING",
                GateCapability.ALERT,
                GateSeverity.BLOCK,
                "risk invalidation rule is not defined",
            )

    def has_block(capability: GateCapability) -> bool:
        return any(
            check.capability == capability and check.severity == GateSeverity.BLOCK
            for check in checks
        )

    can_surface_decision = not has_block(GateCapability.DECISION)
    can_show_target = can_surface_decision and not has_block(GateCapability.TARGET)
    can_enable_alert = can_show_target and not has_block(GateCapability.ALERT)
    outcome = (
        PacketOutcome.BLOCKED
        if not can_surface_decision
        else PacketOutcome.READY_FOR_REVIEW
        if can_enable_alert
        else PacketOutcome.RESEARCH_ONLY
    )
    return TruthGate(
        policy_version=policy.version,
        outcome=outcome,
        can_surface_decision=can_surface_decision,
        can_show_target=can_show_target,
        can_enable_alert=can_enable_alert,
        checks=checks,
    )


def build_decision_packet(
    *,
    packet_id: str,
    recommendation_id: str,
    ticker: str,
    created_at: datetime,
    intent: DecisionIntent,
    rationale: str,
    confidence: DecisionConfidence,
    data: DataTruth,
    forecast: ForecastDistribution | None,
    evidence: ValidationEvidence,
    risk: RiskFrame | None,
    lineage: DecisionLineage,
    policy: DecisionTruthPolicy | None = None,
    warnings: list[str] | None = None,
) -> DecisionPacket:
    """Build a packet with a gate derived from evidence, never caller asserted."""

    gate = evaluate_truth_gate(
        data=data,
        confidence=confidence,
        forecast=forecast,
        evidence=evidence,
        risk=risk,
        lineage=lineage,
        policy=policy,
    )
    return DecisionPacket(
        packet_id=packet_id,
        recommendation_id=recommendation_id,
        ticker=ticker,
        created_at=created_at,
        intent=intent,
        rationale=rationale,
        confidence=confidence,
        data=data,
        forecast=forecast,
        evidence=evidence,
        risk=risk,
        lineage=lineage,
        gate=gate,
        warnings=warnings or [],
    )

