"""The model-lab final verdict is an honest reduction, not advice.

The single most important property: when a passive benchmark wins the
tournament, the verdict must be "no active edge found" — never constructive —
because presenting a passive winner as an active signal overstates exactly what
the models showed. This is the case that occurs most in practice (Buy & Hold
is a strong candidate), so getting it wrong would mislead most of the time.
"""
from __future__ import annotations

from app.services.model_decision import decide_from_tournament, verdict_block


def _tournament(winner, candidates=None, status="complete", rl_status=None):
    return {
        "status": status,
        "candidates": candidates or [winner],
        "winner": winner,
        "n_splits": 3,
        "rl": {"status": rl_status} if rl_status else {},
    }


def test_a_passive_winner_is_never_constructive():
    winner = {
        "key": "buy_hold", "name": "Buy & Hold", "kind": "benchmark",
        "score": 0.792, "per_split_val_sharpe": [3.49, -1.64, 3.09],
    }
    v = decide_from_tournament(_tournament(winner, candidates=[winner] * 8))
    assert v.verdict == "inconclusive"
    assert v.winner_is_passive is True
    assert "no active" in v.headline.lower() or "no active" in " ".join(v.reasons).lower()


def test_a_consistent_positive_active_model_is_constructive():
    winner = {
        "key": "tech_mom", "name": "Tech-momentum only", "kind": "heuristic",
        "score": 0.55, "per_split_val_sharpe": [0.8, 0.4, 0.6],
    }
    v = decide_from_tournament(_tournament(winner, candidates=[winner] * 6))
    assert v.verdict == "constructive"


def test_high_uncertainty_pulls_a_positive_read_to_inconclusive():
    winner = {
        "key": "tech_mom", "name": "Tech-momentum only", "kind": "heuristic",
        "score": 0.55, "per_split_val_sharpe": [0.8, 0.4, 0.6],
    }
    v = decide_from_tournament(
        _tournament(winner, candidates=[winner] * 6), uncertainty_tier="very_high"
    )
    assert v.verdict == "inconclusive"
    assert any("uncertainty" in r for r in v.reasons)


def test_inconsistent_splits_prevent_a_constructive_read():
    winner = {
        "key": "sma", "name": "SMA crossover", "kind": "heuristic",
        "score": 0.30, "per_split_val_sharpe": [3.4, -4.6, 2.8],  # won 2 of 3
    }
    v = decide_from_tournament(_tournament(winner, candidates=[winner] * 6))
    assert v.verdict == "inconclusive"
    assert any("consistent" in r for r in v.reasons)


def test_a_negative_winner_is_cautious():
    winner = {
        "key": "risk", "name": "Risk-quality only", "kind": "heuristic",
        "score": -0.4, "per_split_val_sharpe": [2.1, -2.6, -3.4],
    }
    v = decide_from_tournament(_tournament(winner, candidates=[winner] * 6))
    assert v.verdict == "cautious"


def test_an_incomplete_tournament_is_inconclusive_not_a_guess():
    t = {"status": "insufficient_history", "candidates": [], "winner": None,
         "note": "insufficient history"}
    v = decide_from_tournament(t)
    assert v.verdict == "inconclusive"
    assert "insufficient" in " ".join(v.reasons).lower()


def test_rl_participation_is_reported_when_an_artifact_merged():
    winner = {
        "key": "tech_mom", "name": "Tech-momentum only", "kind": "heuristic",
        "score": 0.55, "per_split_val_sharpe": [0.8, 0.4, 0.6],
    }
    v = decide_from_tournament(
        _tournament(winner, candidates=[winner] * 6, rl_status="artifact_merged")
    )
    assert v.rl_participated is True
    assert any("reinforcement" in r.lower() for r in v.reasons)


def test_the_block_always_carries_the_not_advice_disclaimer():
    winner = {"key": "buy_hold", "name": "Buy & Hold", "kind": "benchmark",
              "score": 0.5, "per_split_val_sharpe": [1.0, 1.0, 1.0]}
    block = verdict_block(_tournament(winner))
    assert "not investment advice" in block["disclaimer"]
    assert block["verdict"] in {"constructive", "cautious", "inconclusive"}
