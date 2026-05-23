"""Phase 19D — passive benchmark (SPY/QQQ) metrics computed alongside the
strategy backtest.

The helper is tested in isolation against a synthetic price series so we
don't need market data fixtures. The schema test guards the contract.
"""
from __future__ import annotations

import math
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from app.services.backtesting import (
    BacktestService,
    DEFAULT_BENCHMARK_TICKERS,
    _calc_calmar,
)


def test_default_benchmark_tickers_are_spy_qqq():
    """Smoke: the headline benchmarks match the upstream FinRL-X README
    comparison (SPY + QQQ)."""
    assert "SPY" in DEFAULT_BENCHMARK_TICKERS
    assert "QQQ" in DEFAULT_BENCHMARK_TICKERS


def test_schema_carries_benchmark_metrics_field():
    """BacktestResultSummary must expose benchmark_metrics so the frontend
    can render the multi-column comparison table."""
    from app.schemas.backtest import BacktestResultSummary, BenchmarkMetricBlock

    fields = BacktestResultSummary.model_fields
    assert "benchmark_metrics" in fields
    # BenchmarkMetricBlock keys mirror the strategy metric keys so the UI can
    # render strategy and benchmark in a single table without key remapping.
    bench_fields = set(BenchmarkMetricBlock.model_fields.keys())
    assert {"total_return", "annualized_return", "max_drawdown", "sharpe_ratio",
            "calmar_ratio", "volatility"}.issubset(bench_fields)


class _FakeRow:
    def __init__(self, bar_date: date, close: float):
        self.bar_date = bar_date
        self.close = close


class _FakeResult:
    def __init__(self, rows: list[_FakeRow]):
        self._rows = rows

    def all(self) -> list[_FakeRow]:
        return self._rows


class _FakeDB:
    """Minimal AsyncSession stand-in: only `execute()` is exercised, and we
    don't need to parse the SQL — every call returns the same row set."""

    def __init__(self, rows: list[_FakeRow]):
        self._rows = rows

    async def execute(self, _query):  # noqa: ARG002 — signature parity only
        return _FakeResult(self._rows)


def _linear_price_series(start: date, days: int, daily_pct: float) -> list[_FakeRow]:
    """Build a synthetic bar series with a constant daily return so the
    resulting Sharpe / vol / DD are derivable analytically."""
    rows = []
    price = 100.0
    for i in range(days + 1):
        rows.append(_FakeRow(start + timedelta(days=i), price))
        price *= 1 + daily_pct
    return rows


@pytest.mark.asyncio
async def test_benchmark_metrics_returns_none_for_missing_ticker():
    """If MarketBar has no rows for the ticker, we return None instead of
    fabricating zero — the UI will render N/A."""
    svc = BacktestService(db=_FakeDB(rows=[]))
    out = await svc._compute_benchmark_metrics(
        ticker="ZZZ",
        rebalance_dates=[date(2026, 1, 1), date(2026, 2, 1)],
        end_date=date(2026, 3, 1),
        periods_per_year=12,
    )
    assert out is None


@pytest.mark.asyncio
async def test_benchmark_metrics_total_return_matches_buy_and_hold():
    """1% daily return over 60 days should land near (1.01^60 - 1) cumulative.

    Series is bar 0..60 (61 bars). end_date is day 60, so we sample 8 weekly
    rebalance points (days 0,7,14,…,49) plus the final day-60 point. The
    benchmark-equivalent equity grows by ≈1% per day → 1.01^60 ≈ 1.8167."""
    rows = _linear_price_series(date(2026, 1, 1), days=60, daily_pct=0.01)
    svc = BacktestService(db=_FakeDB(rows=rows))
    out = await svc._compute_benchmark_metrics(
        ticker="SPY",
        rebalance_dates=[date(2026, 1, 1) + timedelta(days=i * 7) for i in range(8)],
        end_date=date(2026, 3, 1),  # day 59 — last bar with data is day 60 but end_date caps the window
        periods_per_year=52,
    )
    assert out is not None
    # end_date is 2026-03-01 which is day 59 from start; close_at(59) is the bar 59 price.
    # bar 59 price = 100 * 1.01**59
    expected_cum = (1.01 ** 59) - 1
    assert math.isclose(out["total_return"], round(expected_cum, 4), abs_tol=0.01)


@pytest.mark.asyncio
async def test_benchmark_metrics_zero_drawdown_for_monotonic_series():
    """A strictly-monotonic-up series has 0% max drawdown."""
    rows = _linear_price_series(date(2026, 1, 1), days=30, daily_pct=0.005)
    svc = BacktestService(db=_FakeDB(rows=rows))
    out = await svc._compute_benchmark_metrics(
        ticker="SPY",
        rebalance_dates=[date(2026, 1, 1) + timedelta(days=i * 5) for i in range(6)],
        end_date=date(2026, 2, 1),
        periods_per_year=12,
    )
    assert out is not None
    assert out["max_drawdown"] == 0.0
    # Zero drawdown means Calmar is undefined → None per _calc_calmar's contract.
    assert out["calmar_ratio"] is None


@pytest.mark.asyncio
async def test_benchmark_metrics_keys_match_strategy_metrics():
    """Schema parity is what lets the UI render a single multi-column table
    without per-row key remapping."""
    rows = _linear_price_series(date(2026, 1, 1), days=40, daily_pct=0.002)
    svc = BacktestService(db=_FakeDB(rows=rows))
    out = await svc._compute_benchmark_metrics(
        ticker="SPY",
        rebalance_dates=[date(2026, 1, 1) + timedelta(days=i * 7) for i in range(5)],
        end_date=date(2026, 2, 10),
        periods_per_year=52,
    )
    assert out is not None
    assert set(out.keys()) == {
        "total_return", "annualized_return", "max_drawdown", "sharpe_ratio",
        "calmar_ratio", "volatility",
    }


@pytest.mark.asyncio
async def test_benchmark_metrics_under_two_rebalance_dates_returns_none():
    """We need at least 2 sample points to compute any return; degrade
    gracefully rather than dividing by zero."""
    rows = _linear_price_series(date(2026, 1, 1), days=10, daily_pct=0.01)
    svc = BacktestService(db=_FakeDB(rows=rows))
    out = await svc._compute_benchmark_metrics(
        ticker="SPY",
        rebalance_dates=[date(2026, 1, 1)],
        end_date=date(2026, 1, 5),
        periods_per_year=12,
    )
    assert out is None


def test_benchmark_metrics_in_results_summary_source():
    """Literal-source guard: the run_backtest assembly references
    benchmark_metrics in its results_summary dict. If a refactor drops the
    key the UI silently shows nothing, so we flag it at the test layer."""
    from pathlib import Path

    src = (Path(__file__).resolve().parents[1] / "app" / "services" / "backtesting.py").read_text()
    assert '"benchmark_metrics": benchmark_metrics' in src
