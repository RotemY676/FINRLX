"""The three indicators that were computed by unreachable code are now wired.

Review finding 2026-07-23: `_compute_macd_hist`, `_compute_rsi_wilder` and
`_compute_turbulence` existed in `features.py` and were dispatched by key —
but the keys were absent from `DEFAULT_DEFINITIONS`, so no FeatureDefinition
row existed and the dispatch never ran. Meanwhile `desk_elevation` ranked on
those keys, the Desk's risk section filtered for "turbulence", and the dossier
UI labelled rows for RSI and MACD. Three consumers, no producer.

These tests pin the wiring at both ends so the producer cannot disappear again.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.services.features import DEFAULT_DEFINITIONS
from app.services.single_ticker_analysis import Bars, compute_features

WIRED_KEYS = ("rsi_14", "macd_hist_12_26_9", "turbulence_20d")


def _bars(n: int = 300) -> Bars:
    """Weekday closes with enough variation for every indicator to resolve."""
    dates, closes = [], []
    d, px, i = date(2024, 1, 1), 100.0, 0
    while len(dates) < n:
        if d.weekday() < 5:
            px *= 1.0 + (0.006 if (i // 7) % 2 == 0 else -0.004)
            dates.append(d)
            closes.append(round(px, 4))
            i += 1
        d += timedelta(days=1)
    return Bars(dates=dates, closes=closes, volumes=[1_000_000] * n,
                highs=[c * 1.01 for c in closes], lows=[c * 0.99 for c in closes])


@pytest.mark.parametrize("key", WIRED_KEYS)
def test_definition_exists_so_the_dispatch_can_fire(key):
    """The dispatch in FeatureService keys off these; without a definition row
    it is dead code."""
    keys = {d["key"] for d in DEFAULT_DEFINITIONS}
    assert key in keys, f"{key} has a compute function and no definition — unreachable"


@pytest.mark.parametrize("key", WIRED_KEYS)
def test_the_dossier_path_now_produces_them(key):
    bars = _bars()
    feats = compute_features(bars.closes, bars.volumes, [], news_source_exists=False)
    assert key in feats, f"{key} missing from compute_features output"
    value, quality = feats[key]
    assert quality == "ok", f"{key} did not resolve on 300 bars: {quality}"
    assert isinstance(value, float)


def test_rsi_stays_in_its_defined_range():
    bars = _bars()
    rsi, quality = compute_features(
        bars.closes, bars.volumes, [], news_source_exists=False
    )["rsi_14"]
    assert quality == "ok"
    assert 0.0 <= rsi <= 100.0, f"RSI out of range: {rsi}"


def test_turbulence_is_non_negative():
    """It is a squared z-score — negative would mean the maths changed."""
    bars = _bars()
    turb, quality = compute_features(
        bars.closes, bars.volumes, [], news_source_exists=False
    )["turbulence_20d"]
    assert quality == "ok"
    assert turb >= 0.0


@pytest.mark.parametrize("key", WIRED_KEYS)
def test_short_history_reports_insufficient_rather_than_a_number(key):
    """Zero-fiction: too little history must yield None + a reason, not a value."""
    bars = _bars(12)
    value, quality = compute_features(
        bars.closes, bars.volumes, [], news_source_exists=False
    )[key]
    assert value is None
    assert quality == "insufficient_data"


def test_they_appear_in_the_signal_matrix_with_percentile_treatment():
    """Listed in _MATRIX_SPECS = they get percentile + sparkline, not a bare row."""
    from app.services.desk_payload import _MATRIX_SPECS

    spec_keys = {k for k, *_ in _MATRIX_SPECS}
    for key in WIRED_KEYS:
        assert key in spec_keys, (
            f"{key} would fall through to the bare-value tail and lose the "
            "'unusual vs its own history' framing"
        )
