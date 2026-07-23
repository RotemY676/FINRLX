"""Phase 6 — uncertainty moves the threshold instead of annotating the answer.

The market survey identified this as the most decision-useful mechanic in the
industry and the clearest FINRLX gap: confidence existed but never changed what
qualified, so "confidence 0.4" told a reader nothing actionable.

The rule is a stated policy, not a calibrated probability, and these tests pin
the two properties that make it honest: weaker evidence must widen the band
(never narrow it), and a missing input must widen it too — absence of evidence
is not evidence that conditions are benign.
"""
from __future__ import annotations

import pytest

from app.services.uncertainty import (
    BASE_CAUTIOUS,
    BASE_CONSTRUCTIVE,
    TIER_ORDER,
    assess_uncertainty,
    uncertainty_block,
)

CLEAN = {
    "avg_confidence": 0.8,
    "engine_scores": [0.5, 0.55, 0.6],
    "sessions": 400,
    "is_stale": False,
}


def test_clean_evidence_leaves_the_engine_thresholds_alone():
    a = assess_uncertainty(**CLEAN)
    assert a.tier == "low"
    assert a.constructive_at == pytest.approx(BASE_CONSTRUCTIVE)
    assert a.cautious_at == pytest.approx(BASE_CAUTIOUS)


@pytest.mark.parametrize(
    "override,expect_reason",
    [
        ({"avg_confidence": 0.35}, "confidence"),
        ({"avg_confidence": 0.1}, "very low"),
        ({"engine_scores": [-0.5, 0.6]}, "disagree"),
        ({"sessions": 100}, "sessions"),
        ({"is_stale": True}, "stale"),
    ],
)
def test_each_weak_signal_widens_the_band(override, expect_reason):
    weak = assess_uncertainty(**{**CLEAN, **override})
    assert weak.constructive_at > BASE_CONSTRUCTIVE, "the bar must rise, not fall"
    assert weak.cautious_at < BASE_CAUTIOUS
    assert any(expect_reason in r for r in weak.reasons), weak.reasons


@pytest.mark.parametrize("missing", ["avg_confidence", "sessions"])
def test_a_missing_input_widens_the_band_rather_than_being_assumed_benign(missing):
    a = assess_uncertainty(**{**CLEAN, missing: None})
    assert a.tier != "low"
    assert a.constructive_at > BASE_CONSTRUCTIVE


def test_stacked_weakness_reaches_the_widest_tier():
    a = assess_uncertainty(
        avg_confidence=0.05, engine_scores=[-0.9, 0.9], sessions=30, is_stale=True
    )
    assert a.tier == "very_high"
    assert a.tier == TIER_ORDER[-1]


def test_the_band_never_narrows_for_any_input_combination():
    """The mechanic is one-directional by construction — verify it."""
    for conf in (None, 0.0, 0.3, 0.9):
        for spread in ([0.1, 0.2], [-0.9, 0.9], None):
            for sessions in (None, 10, 500):
                for stale in (False, True):
                    a = assess_uncertainty(
                        avg_confidence=conf,
                        engine_scores=spread,
                        sessions=sessions,
                        is_stale=stale,
                    )
                    assert a.constructive_at >= BASE_CONSTRUCTIVE
                    assert a.cautious_at <= BASE_CAUTIOUS


def test_the_same_score_can_earn_a_weaker_stance_under_uncertainty():
    """This is the whole point: uncertainty changes what qualifies."""
    score = 0.32  # clears the base +0.30 bar
    clean = uncertainty_block(composite_score=score, **CLEAN)
    assert clean["stance_under_uncertainty"] == "constructive"

    murky = uncertainty_block(
        composite_score=score,
        avg_confidence=0.2,
        engine_scores=[-0.6, 0.7],
        sessions=90,
        is_stale=True,
    )
    assert murky["stance_under_uncertainty"] == "neutral", (
        "the same score must not clear a widened bar"
    )


def test_the_block_publishes_the_rule_it_applied():
    """The reader must be able to see the rule, like the dial's own thresholds."""
    block = uncertainty_block(composite_score=0.1, **CLEAN)
    assert block["thresholds"]["base"]["constructive_at"] == BASE_CONSTRUCTIVE
    assert "adjusted" in block["thresholds"]
    assert block["reasons"]
    assert "not a calibrated probability" in block["kind"]
    # Inputs are echoed so a claim can be checked against what produced it.
    assert block["inputs"]["avg_confidence"] == CLEAN["avg_confidence"]


def test_disagreement_is_measured_from_real_engine_spread():
    block = uncertainty_block(composite_score=0.0, **{**CLEAN, "engine_scores": [-0.4, 0.5]})
    assert block["inputs"]["engine_score_spread"] == pytest.approx(0.9)


def test_a_single_engine_cannot_produce_a_disagreement_reading():
    """One score has no spread; inventing one would be fiction."""
    block = uncertainty_block(composite_score=0.0, **{**CLEAN, "engine_scores": [0.5]})
    assert block["inputs"]["engine_score_spread"] is None
