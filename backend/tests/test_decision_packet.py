"""P0 gates for the canonical DecisionPacket contract."""
from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from app.schemas.decision_packet import (
    BacktestEvidence,
    CalibrationStatus,
    DataTruth,
    DecisionConfidence,
    DecisionIntent,
    DecisionLineage,
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
from app.services.decision_truth import build_decision_packet

NOW = datetime(2026, 7, 21, 8, 0, tzinfo=UTC)


def _data(**overrides) -> DataTruth:
    values = {
        "data_as_of": NOW,
        "expected_latest_session": date(2026, 7, 20),
        "latest_market_session": date(2026, 7, 20),
        "status": MarketDataStatus.FRESH,
        "lag_trading_days": 0,
        "source_chain": ["primary", "fallback"],
        "selected_source": "primary",
    }
    values.update(overrides)
    return DataTruth(**values)


def _forecast(**overrides) -> ForecastDistribution:
    values = {
        "horizon_trading_days": 21,
        "currency": "usd",
        "p10": 91.0,
        "p50": 104.0,
        "p90": 119.0,
        "generated_at": NOW,
        "model_version": "model-7",
        "calibration_status": CalibrationStatus.VALIDATED,
    }
    values.update(overrides)
    return ForecastDistribution(**values)


def _backtest(**overrides) -> BacktestEvidence:
    values = {
        "backtest_id": "bt-7",
        "status": "completed",
        "source_type": "pipeline_backtest",
        "is_demo": False,
        "lineage_available": True,
        "out_of_sample": True,
        "cost_bps": 10,
        "slippage_bps": 5,
        "observations": 252,
        "start_date": date(2024, 1, 2),
        "end_date": date(2025, 12, 31),
        "promotion_gate_passed": True,
        "promotion_gate_version": "promotion-3",
    }
    values.update(overrides)
    return BacktestEvidence(**values)


def _evidence(**overrides) -> ValidationEvidence:
    values = {
        "backtest": _backtest(),
        "prospective_mode": ProspectiveMode.PAPER,
        "prospective_days": 30,
        "paper_portfolio_id": "paper-4",
    }
    values.update(overrides)
    return ValidationEvidence(**values)


def _lineage(**overrides) -> DecisionLineage:
    values = {
        "data_snapshot_id": "data-1",
        "feature_snapshot_id": "features-2",
        "signal_run_id": "signal-3",
        "model_version": "model-7",
        "policy_version_id": "policy-5",
        "code_version": "5767a5c",
    }
    values.update(overrides)
    return DecisionLineage(**values)


def _build(**overrides):
    values = {
        "packet_id": "packet-1",
        "recommendation_id": "rec-1",
        "ticker": "aapl",
        "created_at": NOW,
        "intent": DecisionIntent.CANDIDATE_ENTRY,
        "rationale": "Candidate for human review; no broker execution is authorized.",
        "confidence": DecisionConfidence(model=0.78, data=0.91, operational=0.88),
        "data": _data(),
        "forecast": _forecast(),
        "evidence": _evidence(),
        "risk": RiskFrame(
            max_position_weight=0.10,
            invalidation_price=87.0,
            invalidation_reason="close below the validated downside boundary",
        ),
        "lineage": _lineage(),
    }
    values.update(overrides)
    return build_decision_packet(**values)


def _codes(packet, capability=None):
    return {
        check.code
        for check in packet.gate.checks
        if capability is None or check.capability == capability
    }


def test_complete_real_evidence_is_ready_for_human_review():
    packet = _build()

    assert packet.ticker == "AAPL"
    assert packet.gate.outcome == PacketOutcome.READY_FOR_REVIEW
    assert packet.gate.can_surface_decision is True
    assert packet.gate.can_show_target is True
    assert packet.gate.can_enable_alert is True
    assert packet.schema_version == "1.0"


@pytest.mark.parametrize(
    ("data", "expected_code"),
    [
        (
            _data(status=MarketDataStatus.STALE, lag_trading_days=3),
            "DATA_NOT_FRESH",
        ),
        (_data(is_demo=True), "DEMO_DATA"),
        (_data(is_synthetic=True), "SYNTHETIC_DATA"),
    ],
)
def test_stale_demo_or_synthetic_data_blocks_all_decision_capabilities(data, expected_code):
    packet = _build(data=data)

    assert packet.gate.outcome == PacketOutcome.BLOCKED
    assert packet.gate.can_surface_decision is False
    assert packet.gate.can_show_target is False
    assert packet.gate.can_enable_alert is False
    assert expected_code in _codes(packet, GateCapability.DECISION)


def test_unvalidated_forecast_keeps_packet_research_only_and_hides_target():
    packet = _build(forecast=_forecast(calibration_status=CalibrationStatus.UNVALIDATED))

    assert packet.gate.outcome == PacketOutcome.RESEARCH_ONLY
    assert packet.gate.can_surface_decision is True
    assert packet.gate.can_show_target is False
    assert packet.gate.can_enable_alert is False
    assert "FORECAST_NOT_VALIDATED" in _codes(packet, GateCapability.TARGET)


def test_demo_backtest_may_not_enable_alerts_even_when_target_is_validated():
    packet = _build(evidence=_evidence(backtest=_backtest(is_demo=True)))

    assert packet.gate.can_surface_decision is True
    assert packet.gate.can_show_target is True
    assert packet.gate.can_enable_alert is False
    assert packet.gate.outcome == PacketOutcome.RESEARCH_ONLY
    assert "BACKTEST_IS_DEMO" in _codes(packet, GateCapability.ALERT)


def test_alerts_require_minimum_prospective_validation_window():
    packet = _build(
        evidence=_evidence(
            prospective_mode=ProspectiveMode.SHADOW,
            prospective_days=5,
            paper_portfolio_id=None,
        )
    )

    assert packet.gate.can_show_target is True
    assert packet.gate.can_enable_alert is False
    assert "PROSPECTIVE_WINDOW_TOO_SHORT" in _codes(packet, GateCapability.ALERT)


def test_disclosed_real_fallback_is_a_warning_not_a_hidden_block():
    packet = _build(
        data=_data(selected_source="fallback", fallback_used=True),
    )

    fallback = next(check for check in packet.gate.checks if check.code == "FALLBACK_DISCLOSED")
    assert fallback.severity == GateSeverity.WARNING
    assert packet.gate.outcome == PacketOutcome.READY_FOR_REVIEW


def test_incomplete_lineage_blocks_decision_surface():
    packet = _build(lineage=_lineage(feature_snapshot_id=None))

    assert packet.gate.outcome == PacketOutcome.BLOCKED
    assert "LINEAGE_INCOMPLETE" in _codes(packet, GateCapability.DECISION)


def test_forecast_quantiles_must_be_ordered():
    with pytest.raises(ValidationError, match="p10 <= p50 <= p90"):
        _forecast(p10=110, p50=100, p90=90)


def test_truth_gate_rejects_caller_asserted_capability_inconsistency():
    with pytest.raises(ValidationError, match="cannot be enabled"):
        TruthGate(
            policy_version="test",
            outcome=PacketOutcome.READY_FOR_REVIEW,
            can_surface_decision=True,
            can_show_target=True,
            can_enable_alert=True,
            checks=[
                GateCheck(
                    code="BACKTEST_MISSING",
                    capability=GateCapability.ALERT,
                    severity=GateSeverity.BLOCK,
                    message="backtest is missing",
                )
            ],
        )


def test_packet_json_is_stable_and_uses_enum_values():
    payload = _build().model_dump(mode="json")

    assert payload["data"]["status"] == "fresh"
    assert payload["forecast"]["calibration_status"] == "validated"
    assert payload["gate"]["outcome"] == "ready_for_review"
    assert payload["created_at"].endswith("Z")

