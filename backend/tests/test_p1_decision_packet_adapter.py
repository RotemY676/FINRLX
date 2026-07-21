"""US-DPK-03 — read-only Recommendation → DecisionPacket adapter (fail-closed).

These exercise the pure adapter with hand-built ORM rows and freshness, so no
DB or network is involved. They assert that the adapter NEVER manufactures an
eligible packet from data the legacy pipeline lacks: synthetic/unknown sources,
missing freshness, incomplete lineage and low confidence all fail closed, while
clean real data with complete lineage surfaces a *research-only* decision
(target + alert still blocked because no forecast/backtest/risk exist).
"""
from __future__ import annotations

from datetime import UTC, date, datetime

from app.models.recommendation import Recommendation, RecommendationWeight
from app.schemas.decision_packet import GateCapability, PacketOutcome
from app.services.decision_packet_adapter import build_recommendation_packets
from app.services.price_freshness import TickerFreshness

NOW = datetime(2026, 7, 21, 12, 0, tzinfo=UTC)
EXPECTED_SESSION = date(2026, 7, 20)
AAPL_ASSET = "asset-aapl"


def _rec(**overrides) -> Recommendation:
    values = dict(
        id="rec-1",
        universe_id="uni-1",
        status="published",
        model_confidence=0.80,
        data_confidence=0.90,
        operational_confidence=0.88,
        data_as_of=datetime(2026, 7, 21, 8, 0, tzinfo=UTC),
        rationale_summary="Research context only; no broker execution authorized.",
        warnings=[],
        # Full lineage so lineage is not the blocking factor unless overridden.
        input_hash="data-snap-1",
        source_feature_set_id="feature-snap-1",
        source_signal_run_ids=["signal-run-1"],
        pipeline_version="pipeline-1.2.3",
        policy_hash="code-abc",
        policy_version_id="policy-9",
    )
    values.update(overrides)
    rec = Recommendation(**values)
    # created_at is normally set by the DB default; emulate it here.
    rec.created_at = overrides.get("created_at", datetime(2026, 7, 21, 8, 5, tzinfo=UTC))
    return rec


def _weight(stance: str = "overweight") -> RecommendationWeight:
    return RecommendationWeight(
        id="w-1", recommendation_id="rec-1", asset_id=AAPL_ASSET,
        target_weight=0.6, stance=stance,
    )


def _fresh(status: str = "fresh", lag: int = 0) -> TickerFreshness:
    return TickerFreshness(
        ticker="AAPL",
        latest_bar_date_iso="2026-07-20",
        lag_trading_days=lag,
        status=status,
    )


def _build(*, rec=None, source="yfinance", freshness=_fresh()):
    return build_recommendation_packets(
        rec=rec or _rec(),
        weights=[_weight()],
        ticker_by_asset={AAPL_ASSET: "AAPL"},
        freshness_by_ticker={"AAPL": freshness} if freshness is not None else {},
        source_by_ticker={"AAPL": source},
        expected_latest_session=EXPECTED_SESSION,
        now=NOW,
    )


def _codes(packet, capability=None):
    return {
        c.code for c in packet.gate.checks
        if capability is None or c.capability == capability
    }


def test_clean_real_data_surfaces_research_only_never_ready():
    # Fresh real data + complete lineage + good confidence, but no forecast /
    # backtest / risk frame → decision surfaces, target + alert stay blocked.
    packet = _build()[0]
    assert packet.packet_id == "dpk:rec-1:AAPL"
    assert packet.recommendation_id == "rec-1"
    assert packet.gate.can_surface_decision is True
    assert packet.gate.can_show_target is False
    assert packet.gate.can_enable_alert is False
    assert packet.gate.outcome == PacketOutcome.RESEARCH_ONLY
    assert "FORECAST_MISSING" in _codes(packet, GateCapability.TARGET)
    assert "BACKTEST_MISSING" in _codes(packet, GateCapability.ALERT)


def test_synthetic_source_blocks_the_decision():
    # The conftest seed uses source="test"; such data must never be eligible.
    packet = _build(source="test")[0]
    assert packet.data.is_synthetic is True
    assert packet.gate.outcome == PacketOutcome.BLOCKED
    assert "SYNTHETIC_DATA" in _codes(packet, GateCapability.DECISION)


def test_demo_source_blocks_the_decision():
    packet = _build(source="demo-provider")[0]
    assert packet.data.is_demo is True
    assert packet.gate.outcome == PacketOutcome.BLOCKED
    assert "DEMO_DATA" in _codes(packet, GateCapability.DECISION)


def test_missing_source_provenance_fails_closed_as_synthetic():
    packet = _build(source=None)[0]
    assert packet.data.selected_source == "unknown"
    assert packet.data.is_synthetic is True
    assert packet.gate.outcome == PacketOutcome.BLOCKED


def test_no_freshness_is_unavailable_and_blocked():
    packet = _build(freshness=None)[0]
    assert packet.data.status.value == "unavailable"
    assert packet.gate.outcome == PacketOutcome.BLOCKED
    assert "DATA_NOT_FRESH" in _codes(packet, GateCapability.DECISION)


def test_stale_data_blocks_the_decision():
    packet = _build(freshness=_fresh(status="stale", lag=4))[0]
    assert packet.gate.outcome == PacketOutcome.BLOCKED
    assert "DATA_NOT_FRESH" in _codes(packet, GateCapability.DECISION)


def test_incomplete_lineage_blocks_the_decision():
    packet = _build(rec=_rec(source_feature_set_id=None))[0]
    assert packet.gate.outcome == PacketOutcome.BLOCKED
    assert "LINEAGE_INCOMPLETE" in _codes(packet, GateCapability.DECISION)


def test_low_confidence_blocks_the_decision():
    packet = _build(rec=_rec(model_confidence=0.10))[0]
    assert packet.gate.outcome == PacketOutcome.BLOCKED
    assert "MODEL_CONFIDENCE_LOW" in _codes(packet, GateCapability.DECISION)


def test_null_confidence_defaults_to_zero_and_blocks():
    packet = _build(rec=_rec(model_confidence=None, data_confidence=None, operational_confidence=None))[0]
    assert packet.gate.outcome == PacketOutcome.BLOCKED


def test_naive_db_timestamps_are_coerced_to_utc_not_rejected():
    # SQLite returns naive datetimes; the adapter must not raise on them.
    rec = _rec(data_as_of=datetime(2026, 7, 21, 8, 0))  # naive
    rec.created_at = datetime(2026, 7, 21, 8, 5)  # naive
    packet = _build(rec=rec)[0]
    assert packet.created_at.tzinfo is not None
    assert packet.data.data_as_of.tzinfo is not None


def test_stance_maps_to_intent():
    for stance, intent in [("overweight", "candidate_entry"), ("exit", "exit"), ("underweight", "candidate_reduce")]:
        pkt = build_recommendation_packets(
            rec=_rec(),
            weights=[_weight(stance=stance)],
            ticker_by_asset={AAPL_ASSET: "AAPL"},
            freshness_by_ticker={"AAPL": _fresh()},
            source_by_ticker={"AAPL": "yfinance"},
            expected_latest_session=EXPECTED_SESSION,
            now=NOW,
        )[0]
        assert pkt.intent.value == intent


def test_unmapped_asset_is_skipped_not_faked():
    packets = build_recommendation_packets(
        rec=_rec(),
        weights=[_weight()],
        ticker_by_asset={},  # asset has no ticker
        freshness_by_ticker={},
        source_by_ticker={},
        expected_latest_session=EXPECTED_SESSION,
        now=NOW,
    )
    assert packets == []
