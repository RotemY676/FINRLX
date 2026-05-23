"""Phase 19G — pricechart returns distinct data per unknown ticker.

Pre-fix bug: every ticker outside the curated CHARTS map (NVDA/AAPL/MSFT)
fell through to a fallback that called _make_chart with start=100, and the
RNG was seeded on `int(start * 100)` — i.e. 10000 for every unknown ticker.
Result: TXN, AMD, INTC, GOOGL all returned the IDENTICAL price series,
return %, and benchmark % (visible in production screenshots on
/research/<ticker>).

Post-fix: the seed is derived from the ticker symbol via SHA-256, and the
synthetic-chart generator picks start/drift/vol per ticker from the same
hash, so each unknown symbol produces its own stable but distinct curve.
"""
from __future__ import annotations

import pytest

from app.api.v1.pricechart import (
    _make_chart,
    _synthetic_chart_for_unknown,
    _ticker_seed,
    CHARTS,
)


def test_ticker_seed_is_stable():
    assert _ticker_seed("TXN") == _ticker_seed("TXN")
    assert _ticker_seed("txn") == _ticker_seed("TXN")  # uppercased


def test_ticker_seed_differs_across_tickers():
    assert _ticker_seed("TXN") != _ticker_seed("AMD")
    assert _ticker_seed("TXN") != _ticker_seed("INTC")


def test_ticker_seed_salt_decorrelates_price_and_benchmark():
    """Without a salt, the price RNG and the benchmark RNG for the same
    ticker would draw from the same stream — making the two lines track."""
    assert _ticker_seed("TXN") != _ticker_seed("TXN", salt="benchmark")


def test_unknown_tickers_produce_distinct_price_series():
    """The original bug, captured as a test."""
    tickers = ["TXN", "AMD", "INTC", "GOOGL", "META", "TSLA"]
    charts = [_synthetic_chart_for_unknown(t) for t in tickers]
    # All 16 weekly closes for each ticker must not match any other ticker.
    series = [tuple(p.price for p in c.points) for c in charts]
    assert len(set(series)) == len(series), (
        "Two unknown tickers produced an identical price series — the "
        "regression from the original bug is back."
    )


def test_unknown_tickers_produce_distinct_returns():
    """The most user-visible facet — the green +X% header."""
    returns = {t: _synthetic_chart_for_unknown(t).price_return_pct for t in
               ["TXN", "AMD", "INTC", "GOOGL", "META", "TSLA"]}
    assert len(set(returns.values())) >= 5, (
        f"Unknown tickers collapsed to too few distinct returns: {returns}"
    )


def test_unknown_tickers_produce_distinct_benchmark_returns():
    """The grey-dashed S&P 500 line was also identical pre-fix — verify it
    varies independently from the price line per ticker."""
    bench_returns = {t: _synthetic_chart_for_unknown(t).benchmark_return_pct
                     for t in ["TXN", "AMD", "INTC", "GOOGL", "META", "TSLA"]}
    assert len(set(bench_returns.values())) >= 4, (
        f"Benchmark returns collapsed: {bench_returns}"
    )


def test_same_ticker_returns_identical_chart_across_calls():
    """The point of the deterministic seed is reproducibility — the same
    ticker queried twice must give the same chart, otherwise replay /
    audit cannot anchor to the value the user actually saw."""
    a = _synthetic_chart_for_unknown("TXN")
    b = _synthetic_chart_for_unknown("TXN")
    assert [p.price for p in a.points] == [p.price for p in b.points]
    assert a.price_return_pct == b.price_return_pct
    assert a.benchmark_return_pct == b.benchmark_return_pct


def test_curated_tickers_still_have_their_explicit_data():
    """NVDA/AAPL/MSFT are pre-baked at module load with curated events;
    the rewrite of _make_chart must not have invalidated that path."""
    assert "NVDA" in CHARTS
    assert "AAPL" in CHARTS
    assert "MSFT" in CHARTS
    assert CHARTS["NVDA"].current_price > 800  # NVDA starts at 920
    assert len(CHARTS["NVDA"].events) == 3      # all 3 curated events preserved


def test_curated_charts_are_distinct_from_each_other():
    """Sanity: the curated entries are not collapsed by the new seeding."""
    nvda = CHARTS["NVDA"]
    aapl = CHARTS["AAPL"]
    msft = CHARTS["MSFT"]
    assert nvda.price_return_pct != aapl.price_return_pct
    assert aapl.price_return_pct != msft.price_return_pct
