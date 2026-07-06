"""Program LEAP S4 — tournament core tests (gates GS4.1 leakage, GS4.2 overfit
rejection, D36 tie-break, failure containment)."""
from __future__ import annotations

import random
from datetime import date, timedelta

from app.services.tournament import (
    multiple_testing_penalty,
    run_tournament,
    score_candidate,
    sharpe,
    walk_forward_splits,
)


def _sessions(n: int, start: date = date(2024, 1, 1)) -> list[date]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


# ── splits: structural leakage guards (GS4.1) ───────────────────────────────


def test_splits_have_no_overlap_and_train_precedes_validation():
    dates = _sessions(200)
    splits = walk_forward_splits(dates, n_splits=3, min_train=60)
    assert len(splits) == 3
    for train, val in splits:
        assert set(train).isdisjoint(val)
        assert max(train) < min(val)


def test_splits_training_windows_expand_monotonically():
    dates = _sessions(200)
    splits = walk_forward_splits(dates, n_splits=3)
    sizes = [len(t) for t, _ in splits]
    assert sizes == sorted(sizes) and sizes[0] < sizes[-1]


def test_splits_insufficient_history_yields_empty():
    assert walk_forward_splits(_sessions(61), n_splits=3, min_train=60) == []


def test_splits_reject_unsorted_dates():
    dates = _sessions(100)
    dates[0], dates[1] = dates[1], dates[0]
    try:
        walk_forward_splits(dates)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


# ── scoring (D36) ───────────────────────────────────────────────────────────


def test_sharpe_degenerate_inputs_are_zero():
    assert sharpe([]) == 0.0
    assert sharpe([0.01]) == 0.0
    assert sharpe([0.01] * 50) == 0.0  # zero variance


def test_multiple_testing_penalty_grows_with_candidates():
    assert multiple_testing_penalty(1) == 0.0
    assert 0 < multiple_testing_penalty(3) < multiple_testing_penalty(10)


def test_divergence_penalty_only_hits_overfit_direction():
    good_val = [0.002] * 100 + [-0.001] * 60
    better_val_than_train = score_candidate([0.0] * 100, good_val, 1)
    assert better_val_than_train["divergence"] == 0.0  # val > train: no penalty
    overfit = score_candidate(good_val, [0.0] * 100, 1)
    assert overfit["divergence_penalty"] > 0


# ── the core honesty test: overfit candidate must lose (GS4.2) ──────────────


def test_deliberately_overfit_candidate_is_rejected():
    """A memorizer that is spectacular on training dates and useless on unseen
    dates must lose to an honest modest candidate, despite a far higher
    train Sharpe."""
    dates = _sessions(240)
    splits = walk_forward_splits(dates, n_splits=3, min_train=100)
    train_windows = [frozenset(t) for t, _ in splits]

    rng_o = random.Random(11)

    def overfit_memorizer(window: list[date]) -> list[float]:
        # Behaves like a model that fit its training window perfectly:
        # strong steady returns in-sample, zero-mean noise out-of-sample.
        in_sample = any(set(window) <= tw for tw in train_windows)
        if in_sample:
            return [0.008 + rng_o.gauss(0, 0.002) for _ in window]
        return [rng_o.gauss(0, 0.006) for _ in window]

    rng = random.Random(7)

    def honest_modest(window: list[date]) -> list[float]:
        return [0.0006 + rng.gauss(0, 0.004) for _ in window]

    result = run_tournament(
        {
            "memorizer": ("ml", overfit_memorizer),
            "modest": ("heuristic", honest_modest),
        },
        splits,
    )
    by = {c.name: c for c in result.candidates}
    assert by["memorizer"].aggregate["train_sharpe"] > by["memorizer"].aggregate["validation_sharpe"]
    assert by["memorizer"].aggregate["divergence_penalty"] > 1.0
    assert result.winner == "modest"
    assert "penalty" in result.rationale


def test_tie_breaks_toward_simpler_complexity():
    dates = _sessions(240)
    splits = walk_forward_splits(dates, n_splits=3, min_train=100)
    same = lambda window: [0.001] * len(window) + ([0.002] if window else [])  # noqa: E731

    def identical(window: list[date]) -> list[float]:
        rng = random.Random(42)  # same seed => identical streams
        return [0.001 + rng.gauss(0, 0.003) for _ in window]

    def identical2(window: list[date]) -> list[float]:
        rng = random.Random(42)
        return [0.001 + rng.gauss(0, 0.003) for _ in window]

    result = run_tournament(
        {"rl_agent": ("rl", identical), "simple_rule": ("heuristic", identical2)},
        splits,
    )
    assert result.winner == "simple_rule"
    assert "tie" in result.rationale


def test_failing_candidate_is_contained_and_cannot_win():
    dates = _sessions(200)
    splits = walk_forward_splits(dates, n_splits=2, min_train=100)

    def exploder(window: list[date]) -> list[float]:
        raise RuntimeError("candidate blew up")

    rng = random.Random(3)

    def ok(window: list[date]) -> list[float]:
        return [0.0005 + rng.gauss(0, 0.004) for _ in window]

    result = run_tournament(
        {"boom": ("rl", exploder), "steady": ("heuristic", ok)}, splits
    )
    by = {c.name: c for c in result.candidates}
    assert by["boom"].status == "failed"
    assert result.winner == "steady"


def test_no_splits_yields_honest_no_winner():
    result = run_tournament({"x": ("heuristic", lambda w: [0.0] * len(w))}, [])
    assert result.winner is None
    assert "insufficient history" in result.rationale


def test_disclaimers_always_present():
    dates = _sessions(200)
    splits = walk_forward_splits(dates, n_splits=2, min_train=100)
    result = run_tournament({"x": ("heuristic", lambda w: [0.001] * len(w))}, splits)
    joined = " ".join(result.disclaimers).lower()
    assert "not investment advice" in joined
    assert "past performance" in joined
