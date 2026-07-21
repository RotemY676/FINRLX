"""Read-only projection of a legacy Recommendation into canonical DecisionPackets.

US-DPK-03 (current adapter) scaffolding, gated by ``decision_packet_v1``.

This maps the *existing* decision-pipeline output — a ``Recommendation`` plus its
per-asset weights and the *real* price-freshness of each ticker — onto the P1
``DecisionPacket`` contract WITHOUT fabricating evidence. Anything the pipeline
does not actually hold (a calibrated forecast, a reproducible backtest,
prospective validation, a risk frame, full lineage) stays absent, so the truth
gate honestly reports ``blocked`` or ``research_only``. Nothing in this module
can manufacture a ``ready_for_review`` packet from data the pipeline lacks.

The function is deliberately pure: it takes already-fetched values so it can be
unit-tested without a database or network.
"""
from __future__ import annotations

from datetime import UTC, date, datetime

from app.models.recommendation import Recommendation, RecommendationWeight
from app.schemas.decision_packet import (
    DataTruth,
    DecisionConfidence,
    DecisionIntent,
    DecisionLineage,
    DecisionPacket,
    MarketDataStatus,
    ValidationEvidence,
)
from app.services.decision_truth import build_decision_packet
from app.services.price_freshness import TickerFreshness

# US-P0-06 zero-fiction: only an explicit ALLOWLIST of real providers may back an
# eligible decision. Everything else fails closed. A denylist (the previous
# design) silently promoted unrecognised labels — e.g. the beta generator's
# "local" — to trustworthy market evidence, which contradicts the stated intent
# ("unknown provenance is treated as non-real") and the P0 rule that no missing
# field may silently default to a pass.
#
# Real providers map to live fetches in ingest.py: "yfinance" and the on-chain
# price provider ("chain" == chain_provider.CHAIN_SOURCE). The deterministic beta
# generator ("local"/"local_deterministic"), fixtures, test seeds, and any
# unknown or missing label are non-real → synthetic → blocked.
_REAL_SOURCE_TOKENS = ("yfinance", "chain")
# Non-real labels that are specifically demos get the more precise DEMO reason
# code (matched as substrings) instead of the generic synthetic one.
_DEMO_SOURCE_TOKENS = ("demo", "sample", "example", "placeholder")

_FRESHNESS_TO_STATUS = {
    "fresh": MarketDataStatus.FRESH,
    "stale": MarketDataStatus.STALE,
    "degraded": MarketDataStatus.DEGRADED,
}


def _aware(value: datetime | None, *, fallback: datetime) -> datetime:
    """Coerce a possibly-naive DB timestamp to a timezone-aware UTC datetime.

    SQLite hands back naive datetimes even for ``DateTime(timezone=True)``
    columns; the packet contract requires tz-aware timestamps. We assume UTC
    (the storage convention) rather than inventing an offset.
    """
    dt = value or fallback
    if dt.tzinfo is None or dt.utcoffset() is None:
        return dt.replace(tzinfo=UTC)
    return dt


def _classify_source(source: str | None) -> tuple[bool, bool]:
    """Return (is_demo, is_synthetic) for a market-data source label.

    Fail-closed by allowlist: only an explicit real provider passes. Any other
    label — the beta "local" generator, fixtures, test seeds, or unknown/missing
    provenance — is synthetic and cannot back an eligible decision (US-P0-06).
    """
    token = (source or "").strip().lower()
    is_demo = any(t in token for t in _DEMO_SOURCE_TOKENS)
    is_synthetic = token not in _REAL_SOURCE_TOKENS
    return (is_demo, is_synthetic)


def _intent_from_stance(stance: str | None) -> DecisionIntent:
    normalized = (stance or "").strip().lower()
    return {
        "overweight": DecisionIntent.CANDIDATE_ENTRY,
        "buy": DecisionIntent.CANDIDATE_ENTRY,
        "long": DecisionIntent.CANDIDATE_ENTRY,
        "underweight": DecisionIntent.CANDIDATE_REDUCE,
        "reduce": DecisionIntent.CANDIDATE_REDUCE,
        "exit": DecisionIntent.EXIT,
        "sell": DecisionIntent.EXIT,
        "neutral": DecisionIntent.HOLD,
        "hold": DecisionIntent.HOLD,
        "avoid": DecisionIntent.AVOID,
    }.get(normalized, DecisionIntent.OBSERVE)


def _build_data_truth(
    *,
    freshness: TickerFreshness | None,
    source: str | None,
    expected_latest_session: date,
    data_as_of: datetime,
) -> DataTruth:
    quality_warnings: list[str] = []

    if freshness is None:
        # No ingested bars for this ticker: fail closed as UNAVAILABLE.
        return DataTruth(
            data_as_of=data_as_of,
            expected_latest_session=expected_latest_session,
            latest_market_session=None,
            status=MarketDataStatus.UNAVAILABLE,
            lag_trading_days=None,
            source_chain=[],
            selected_source=None,
            quality_warnings=["no ingested price bars for this ticker"],
        )

    is_demo, is_synthetic = _classify_source(source)
    resolved_source = source
    if not (source or "").strip():
        # Preserve schema invariants (FRESH requires a selected_source) while
        # still failing the gate via is_synthetic below.
        resolved_source = "unknown"
        quality_warnings.append("price source provenance missing; treated as non-real")

    return DataTruth(
        data_as_of=data_as_of,
        expected_latest_session=expected_latest_session,
        latest_market_session=date.fromisoformat(freshness.latest_bar_date_iso),
        status=_FRESHNESS_TO_STATUS.get(freshness.status, MarketDataStatus.DEGRADED),
        lag_trading_days=freshness.lag_trading_days,
        source_chain=[resolved_source] if resolved_source else [],
        selected_source=resolved_source,
        is_demo=is_demo,
        is_synthetic=is_synthetic,
        quality_warnings=quality_warnings,
    )


def _build_lineage(rec: Recommendation) -> DecisionLineage:
    signal_run_ids = rec.source_signal_run_ids or []
    first_signal_run = signal_run_ids[0] if isinstance(signal_run_ids, list) and signal_run_ids else None
    return DecisionLineage(
        data_snapshot_id=rec.input_hash,
        feature_snapshot_id=rec.source_feature_set_id,
        signal_run_id=first_signal_run,
        model_version=rec.pipeline_version,
        policy_version_id=rec.policy_version_id,
        code_version=rec.policy_hash,
    )


def build_recommendation_packets(
    *,
    rec: Recommendation,
    weights: list[RecommendationWeight],
    ticker_by_asset: dict[str, str],
    freshness_by_ticker: dict[str, TickerFreshness],
    source_by_ticker: dict[str, str | None],
    expected_latest_session: date,
    now: datetime,
) -> list[DecisionPacket]:
    """Project a recommendation and its weights into one packet per weighted asset.

    Evidence that the legacy pipeline does not carry is left absent on purpose;
    the truth gate — not this adapter — decides eligibility.
    """
    created_at = _aware(rec.created_at, fallback=now)
    data_as_of = _aware(rec.data_as_of, fallback=created_at)
    lineage = _build_lineage(rec)
    rec_warnings = rec.warnings if isinstance(rec.warnings, list) else []

    confidence = DecisionConfidence(
        model=rec.model_confidence if rec.model_confidence is not None else 0.0,
        data=rec.data_confidence if rec.data_confidence is not None else 0.0,
        operational=rec.operational_confidence if rec.operational_confidence is not None else 0.0,
    )

    packets: list[DecisionPacket] = []
    for weight in weights:
        ticker = ticker_by_asset.get(weight.asset_id)
        if not ticker:
            # An unmapped asset cannot be surfaced as a decision; skip rather
            # than invent a ticker.
            continue

        data = _build_data_truth(
            freshness=freshness_by_ticker.get(ticker),
            source=source_by_ticker.get(ticker),
            expected_latest_session=expected_latest_session,
            data_as_of=data_as_of,
        )

        rationale = (
            rec.rationale_summary
            or f"Research projection of recommendation {rec.id}; no broker execution is authorized."
        )

        packet = build_decision_packet(
            packet_id=f"dpk:{rec.id}:{ticker}",
            recommendation_id=rec.id,
            ticker=ticker,
            created_at=created_at,
            intent=_intent_from_stance(weight.stance),
            rationale=rationale,
            confidence=confidence,
            data=data,
            forecast=None,  # no calibrated ForecastDistribution in the legacy pipeline
            evidence=ValidationEvidence(),  # no linked backtest / prospective validation
            risk=None,  # no explicit risk frame in the legacy pipeline
            lineage=lineage,
            warnings=list(rec_warnings),
        )
        packets.append(packet)

    return packets
