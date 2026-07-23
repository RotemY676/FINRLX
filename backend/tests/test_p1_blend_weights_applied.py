"""Blend weights must actually change the allocation.

Review finding 2026-07-23: `_score_weighted_agent_fn(blend_weights)` accepted
the weights and never referenced them. Every "trained" policy snapshot produced
byte-identical output to the untrained heuristic baseline, while
`evaluate_policy` reported `used_policy_weights: True`.

The weights were unusable by construction: `build_state` averaged the engine
scores into a single number before any agent saw them, even though the state
schema had always declared an `engine_scores` field. The builder now emits it
and the agent blends over it.

These tests pin the property that was missing — that different weights produce
different allocations — rather than just the presence of a parameter.
"""
from __future__ import annotations

import pytest

from app.services.rl_training import (
    _score_weighted_agent_fn,
    agent_uses_blend_weights,
    blended_score,
)

CONSTRAINTS = {"position_cap_max": 0.5, "cash_floor": 0.05, "max_invested": 0.95}


def _state() -> dict:
    """Two assets whose engines disagree in opposite directions.

    The disagreement is the point: if weights are ignored, both tickers keep
    the same relative allocation no matter how the weights are set.
    """
    return {
        "assets": [
            {
                "ticker": "AAA",
                "engine_score": 0.5,
                "engine_scores": {"technical_momentum": 0.9, "risk_quality": 0.1},
            },
            {
                "ticker": "BBB",
                "engine_score": 0.5,
                "engine_scores": {"technical_momentum": 0.1, "risk_quality": 0.9},
            },
        ]
    }


def test_blended_score_follows_the_weights():
    asset = _state()["assets"][0]
    momentum_heavy = blended_score(asset, {"technical_momentum": 1.0, "risk_quality": 0.0})
    risk_heavy = blended_score(asset, {"technical_momentum": 0.0, "risk_quality": 1.0})
    assert momentum_heavy == pytest.approx(0.9)
    assert risk_heavy == pytest.approx(0.1)


def test_different_weights_produce_different_allocations():
    """The regression that mattered: the agent's OUTPUT must change."""
    state = _state()
    momentum = _score_weighted_agent_fn({"technical_momentum": 1.0, "risk_quality": 0.0})
    risk = _score_weighted_agent_fn({"technical_momentum": 0.0, "risk_quality": 1.0})

    w_momentum = momentum(state, CONSTRAINTS)["target_weights"]
    w_risk = risk(state, CONSTRAINTS)["target_weights"]

    assert w_momentum != w_risk, "weights are being ignored — the original bug"
    # Momentum-weighted favours AAA; risk-weighted favours BBB.
    assert w_momentum["AAA"] > w_momentum["BBB"]
    assert w_risk["BBB"] > w_risk["AAA"]


def test_falls_back_honestly_when_per_engine_detail_is_absent():
    """Older states carry only the average; the blend must degrade, not invent."""
    legacy = {"assets": [{"ticker": "AAA", "engine_score": 0.42}]}
    assert blended_score(legacy["assets"][0], {"technical_momentum": 1.0}) == pytest.approx(0.42)
    assert agent_uses_blend_weights(legacy, {"technical_momentum": 1.0}) is False


def test_reports_use_only_when_the_weights_can_bite():
    """`used_policy_weights` must describe reality, not intent."""
    assert agent_uses_blend_weights(_state(), {"technical_momentum": 1.0}) is True
    assert agent_uses_blend_weights(_state(), {}) is False


def test_unknown_engine_names_do_not_silently_zero_the_score():
    """Weights naming engines the state lacks must fall back, not return 0."""
    asset = _state()["assets"][0]
    assert blended_score(asset, {"not_an_engine": 1.0}) == pytest.approx(0.5)
