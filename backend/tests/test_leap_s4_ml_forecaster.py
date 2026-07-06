"""Program LEAP S4 — ML forecaster tests (D35b + leakage guards GS4.1)."""
from __future__ import annotations

import math
import random

from app.services.ml_forecaster import (
    DEFAULT_HORIZON,
    build_matrix,
    fit_forecaster,
    predict_latest,
)


def _momentum_series(n: int = 500, seed: int = 5) -> list[float]:
    """Synthetic series with a real momentum signal: recent 20d trend carries
    forward, plus noise — learnable, not memorizable."""
    rng = random.Random(seed)
    closes = [100.0]
    drift = 0.0
    for _ in range(n - 1):
        drift = 0.95 * drift + rng.gauss(0, 0.002)
        closes.append(closes[-1] * (1.0 + drift + rng.gauss(0, 0.005)))
    return closes


def test_build_matrix_rows_never_touch_future_features():
    closes = _momentum_series(300)
    X, y, idxs = build_matrix(closes, horizon=20)
    assert len(X) == len(y) == len(idxs) > 0
    # Every training row's index leaves a full 20-session label window inside
    # the series, and the last `horizon` sessions produce no rows at all.
    assert max(idxs) <= len(closes) - 20 - 1
    # Perturbing the future must not change the feature row for an index.
    t = idxs[len(idxs) // 2]
    mutated = list(closes)
    for j in range(t + 1, len(mutated)):
        mutated[j] *= 3.7
    X2, _, idxs2 = build_matrix(mutated, horizon=20)
    row, row2 = X[idxs.index(t)], X2[idxs2.index(t)]
    assert row == row2


def test_fit_returns_none_on_insufficient_history():
    assert fit_forecaster(_momentum_series(150)) is None


def test_fit_learns_momentum_in_aggregate_across_seeds():
    """Out-of-sample MSE vs an always-zero predictor, pooled over 5 seeds.

    Single synthetic paths have only ~80 overlapping holdout points, so
    per-path outcomes are luck-dominated; genuine skill must show in the
    aggregate ratio (< 1.0). Individual-path variance is expected and honest.
    """
    total_model, total_zero, total_n = 0.0, 0.0, 0
    for seed in (1, 2, 3, 5, 9):
        closes = _momentum_series(500, seed=seed)
        holdout_start = 400
        fit = fit_forecaster(closes[:holdout_start])
        assert fit is not None and fit.n_rows >= 120
        for t in range(holdout_start, len(closes) - DEFAULT_HORIZON):
            pred = predict_latest(fit, closes[: t + 1])
            realized = closes[t + DEFAULT_HORIZON] / closes[t] - 1.0
            if pred is None:
                continue
            total_model += (pred - realized) ** 2
            total_zero += realized ** 2
            total_n += 1
    assert total_n > 300
    assert total_model / total_zero < 1.0


def test_predict_latest_is_finite_and_bounded():
    closes = _momentum_series(500)
    fit = fit_forecaster(closes)
    pred = predict_latest(fit, closes)
    assert pred is not None and math.isfinite(pred)
    assert abs(pred) < 1.0  # a 20d return prediction beyond ±100% is nonsense


def test_deterministic_given_seed_and_data():
    closes = _momentum_series(400)
    p1 = predict_latest(fit_forecaster(closes), closes)
    p2 = predict_latest(fit_forecaster(closes), closes)
    assert p1 == p2
