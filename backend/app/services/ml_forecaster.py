"""Program LEAP S4 — real ML return forecaster (decision D35b).

Implements the model behind the long-stubbed `ml_return_forecaster` engine:
a HistGradientBoostingRegressor predicting next-`horizon`-session returns
from strictly lagged price-derived features.

Leakage discipline (GS4.1): the feature row for session t uses closes up to
and including t only; its label is the realized return over (t, t+horizon].
Rows whose label window extends past the data end are excluded from training.

DB-free by design: callers (autopilot S2, tournament S4) pass closes aligned
to sessions; persistence of predictions into model_predictions stays with the
existing ml_* services.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

MODEL_KEY = "ml_return_forecaster"
MODEL_VERSION = "leap-s4.1"
DEFAULT_HORIZON = 20
MIN_TRAIN_ROWS = 120
_FEATURE_LOOKBACKS = (1, 5, 20, 60)
_VOL_LOOKBACK = 20

__all__ = [
    "MODEL_KEY",
    "MODEL_VERSION",
    "ForecasterFit",
    "build_matrix",
    "fit_forecaster",
    "predict_latest",
]


def _trailing_return(closes: Sequence[float], idx: int, lookback: int) -> float | None:
    if idx - lookback < 0 or closes[idx - lookback] == 0:
        return None
    return closes[idx] / closes[idx - lookback] - 1.0


def _trailing_vol(closes: Sequence[float], idx: int, lookback: int) -> float | None:
    if idx - lookback < 1:
        return None
    rets = [
        closes[i] / closes[i - 1] - 1.0
        for i in range(idx - lookback + 1, idx + 1)
        if closes[i - 1] != 0
    ]
    if len(rets) < 2:
        return None
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var)


def build_matrix(
    closes: Sequence[float], horizon: int = DEFAULT_HORIZON
) -> tuple[list[list[float]], list[float], list[int]]:
    """(X, y, row_indices) with strictly-lagged features and forward labels.

    Row for index t exists only when every feature lookback is available AND
    the full label window t+horizon is inside the series — so no row can peek
    forward, and the most recent `horizon` sessions are never trained on.
    """
    X: list[list[float]] = []
    y: list[float] = []
    idxs: list[int] = []
    max_lb = max(*_FEATURE_LOOKBACKS, _VOL_LOOKBACK)
    for t in range(max_lb, len(closes) - horizon):
        feats = [_trailing_return(closes, t, lb) for lb in _FEATURE_LOOKBACKS]
        feats.append(_trailing_vol(closes, t, _VOL_LOOKBACK))
        if any(f is None for f in feats):
            continue
        if closes[t] == 0:
            continue
        label = closes[t + horizon] / closes[t] - 1.0
        X.append([float(f) for f in feats])  # type: ignore[arg-type]
        y.append(label)
        idxs.append(t)
    return X, y, idxs


@dataclass
class ForecasterFit:
    model: object
    horizon: int
    n_rows: int
    train_score_r2: float
    version: str = MODEL_VERSION


def fit_forecaster(
    closes: Sequence[float],
    horizon: int = DEFAULT_HORIZON,
    random_state: int = 42,
) -> ForecasterFit | None:
    """Fit on all eligible rows; None when history is insufficient (honest)."""
    from sklearn.ensemble import HistGradientBoostingRegressor

    X, y, _ = build_matrix(closes, horizon)
    if len(X) < MIN_TRAIN_ROWS:
        return None
    # Heavily regularized on purpose: financial return targets are mostly
    # noise, and the LEAP tournament's divergence penalty punishes anything
    # that memorizes its training window (verified in the S4 test suite).
    model = HistGradientBoostingRegressor(
        max_depth=1,
        max_iter=30,
        learning_rate=0.08,
        l2_regularization=5.0,
        min_samples_leaf=60,
        random_state=random_state,
    )
    model.fit(X, y)
    return ForecasterFit(
        model=model,
        horizon=horizon,
        n_rows=len(X),
        train_score_r2=float(model.score(X, y)),
    )


def predict_latest(fit: ForecasterFit, closes: Sequence[float]) -> float | None:
    """Predicted forward `horizon`-session return from the latest session."""
    t = len(closes) - 1
    feats = [_trailing_return(closes, t, lb) for lb in _FEATURE_LOOKBACKS]
    feats.append(_trailing_vol(closes, t, _VOL_LOOKBACK))
    if any(f is None for f in feats):
        return None
    return float(fit.model.predict([[float(f) for f in feats]])[0])  # type: ignore[list-item]
