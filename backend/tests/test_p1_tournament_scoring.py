"""The autopilot tournament actually scores candidates (regression).

Found 2026-07-23 while speccing the RL comparison dashboard: on 515 fresh bars,
every one of the 8 tournament candidates scored val_sharpe 0.0 across all three
walk-forward splits. Cause: `_sharpe_of` read `metrics.get("sharpe")`, but
`run_strategy` emits the Sharpe under `sharpe_ratio`. The lookup was always
None -> 0.0, so the "winner" collapsed to whichever candidate the tie-break
surfaced (all rows equal to -deflation_penalty). The product's flagship
walk-forward model selection had been inert, and the split-consistency strip
rendered [0,0,0] for every model.

These tests pin the property that was missing: the tournament must actually
differentiate candidates, and _sharpe_of must read the key run_strategy writes.
"""
from __future__ import annotations

from datetime import date, timedelta

from app.services.autopilot import (
    _sharpe_of,
    build_candidates,
    run_tournament,
    walk_forward_splits,
)
from app.services.single_ticker_analysis import (
    Bars,
    _generate_weekly_rebalances,
    precompute_rebalance_states,
    run_strategy,
    StrategyDef,
)


def _trending_bars(n: int = 520) -> Bars:
    """Weekday closes with real regime variation so Sharpe is well-defined."""
    dates, closes = [], []
    d, px, i = date(2024, 1, 1), 100.0, 0
    while len(dates) < n:
        if d.weekday() < 5:
            # alternating trends give non-zero, non-constant returns
            drift = 0.006 if (i // 30) % 2 == 0 else -0.004
            px *= 1.0 + drift + (0.002 if i % 3 == 0 else -0.001)
            dates.append(d)
            closes.append(round(px, 4))
            i += 1
        d += timedelta(days=1)
    return Bars(dates=dates, closes=closes, volumes=[1_000_000] * n,
                highs=[c * 1.01 for c in closes], lows=[c * 0.99 for c in closes])


def _states():
    bars = _trending_bars()
    rebs = _generate_weekly_rebalances(bars.dates[0], bars.dates[-1])
    return precompute_rebalance_states(bars, [], rebs)


def test_sharpe_of_reads_the_key_run_strategy_actually_writes():
    """The exact defect: the metrics key must be the one run_strategy emits."""
    states = _states()
    # A long-only decide over a trending series has a defined, non-zero Sharpe.
    metrics = run_strategy(states, StrategyDef("t", "t", "t", "#000", "", lambda s: 1.0)).get("metrics", {})
    assert "sharpe_ratio" in metrics
    assert metrics.get("sharpe") is None, (
        "if run_strategy ever adds a 'sharpe' key, revisit _sharpe_of"
    )
    # _sharpe_of must surface a real number, not silently swallow the mismatch.
    val = _sharpe_of(states[: len(states) // 2], lambda s: 1.0)
    assert val != 0.0


def test_the_tournament_differentiates_candidates():
    """Not all-zero: real walk-forward validation must spread the field."""
    states = _states()
    assert walk_forward_splits(len(states)), "fixture must have enough states"
    result = run_tournament(states, ticker="TST")

    cands = result["candidates"]
    assert len(cands) >= 6
    val_sharpes = [c["val_sharpe"] for c in cands]
    scores = [c["score"] for c in cands]

    # The regression: every value was exactly 0.0.
    assert any(v != 0.0 for v in val_sharpes), "all candidates scored 0 — tournament is inert"
    assert len(set(scores)) > 1, "candidates must be differentiated, not all tied"


def test_per_split_values_are_not_uniformly_zero():
    """The split-consistency strip depends on these being real."""
    states = _states()
    result = run_tournament(states, ticker="TST")
    winner = result["winner"]
    assert winner is not None
    splits = winner.get("per_split_val_sharpe") or []
    assert splits, "winner must carry per-split validation Sharpes"
    assert any(s != 0.0 for s in splits), "per-split Sharpes were all zero"


def test_a_winner_is_selected_by_score_not_tie_break():
    """With differentiated scores the winner is the genuine argmax."""
    states = _states()
    result = run_tournament(states, ticker="TST")
    winner = result["winner"]
    best = max(result["candidates"], key=lambda c: c["score"])
    assert winner["key"] == best["key"]
