"""Phase B1 — risk_metrics service contract tests.

Exercises the four internal compute paths with deterministic inputs so
the math is locked. Hits the API layer once at the end to confirm the
endpoint returns the expected shape.
"""
from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.services.risk_metrics import RiskMetricsService, _stddev


def _make_snapshot(value: float, daily_return: float | None = None, max_dd: float | None = None):
    return SimpleNamespace(
        portfolio_value=value,
        daily_return=daily_return,
        max_drawdown_to_date=max_dd,
    )


def test_stddev_basic():
    assert _stddev([1.0, 1.0, 1.0]) == 0.0
    # known: std of [1,2,3] (sample) = 1.0
    assert abs(_stddev([1.0, 2.0, 3.0]) - 1.0) < 1e-9


def test_concentration_groups_by_sector():
    svc = RiskMetricsService(db=None)  # type: ignore[arg-type]
    holdings = {
        "a1": {"ticker": "AAA", "current_weight": 0.40},
        "a2": {"ticker": "BBB", "current_weight": 0.30},
        "a3": {"ticker": "CCC", "current_weight": 0.20},
        "a4": {"ticker": "DDD", "current_weight": 0.10},
    }
    sectors = {"a1": "Tech", "a2": "Tech", "a3": "Health", "a4": "Health"}
    out = svc._concentration(holdings, sectors)
    assert out["total_positions"] == 4
    assert out["top1_weight"] == 0.40
    assert out["top3_weight"] == pytest.approx(0.90)
    assert out["top5_weight"] == pytest.approx(1.00)
    tech = next(s for s in out["sectors"] if s["sector"] == "Tech")
    health = next(s for s in out["sectors"] if s["sector"] == "Health")
    assert tech["weight"] == pytest.approx(0.70)
    assert health["weight"] == pytest.approx(0.30)


def test_drawdown_uses_running_peak_when_field_missing():
    svc = RiskMetricsService(db=None)  # type: ignore[arg-type]
    # Series 100 -> 120 (peak) -> 90 -> 110. Current dd = (110-120)/120 ≈ -0.0833
    snaps = [
        _make_snapshot(100.0),
        _make_snapshot(120.0),
        _make_snapshot(90.0),
        _make_snapshot(110.0),
    ]
    out = svc._drawdown(snaps)
    assert out["peak_value"] == 120.0
    assert out["current_value"] == 110.0
    assert out["current_drawdown"] == pytest.approx(-0.0833, abs=1e-4)
    # max_drawdown via running peak: 120 -> 90 is -25%
    assert out["max_drawdown"] == pytest.approx(-0.25, abs=1e-4)


def test_drawdown_uses_field_when_present():
    svc = RiskMetricsService(db=None)  # type: ignore[arg-type]
    snaps = [_make_snapshot(100.0, max_dd=None), _make_snapshot(80.0, max_dd=-0.20)]
    out = svc._drawdown(snaps)
    # Last snapshot's max_drawdown_to_date wins
    assert out["max_drawdown"] == -0.20


def test_var_parametric():
    svc = RiskMetricsService(db=None)  # type: ignore[arg-type]
    # Returns with stddev 0.01 → VaR95 = 1.6449 * 0.01 ≈ 0.01645
    snaps = [_make_snapshot(1.0, daily_return=r) for r in [-0.01, 0.01, -0.01, 0.01, -0.01, 0.01]]
    out = svc._var(snaps)
    assert out["sample_size"] == 6
    assert out["volatility_daily"] == pytest.approx(0.01095, abs=1e-4)  # sample stddev
    assert out["var_95"] == pytest.approx(1.6449 * out["volatility_daily"], abs=1e-6)
    assert out["var_99"] == pytest.approx(2.3263 * out["volatility_daily"], abs=1e-6)


def test_var_too_few_samples_returns_zeros():
    svc = RiskMetricsService(db=None)  # type: ignore[arg-type]
    out = svc._var([_make_snapshot(1.0, daily_return=0.01)])
    assert out["sample_size"] == 1
    assert out["var_95"] == 0.0


def test_exposure_long_only():
    svc = RiskMetricsService(db=None)  # type: ignore[arg-type]
    holdings = {
        "a1": {"current_weight": 0.5},
        "a2": {"current_weight": 0.3},
    }
    out = svc._exposure(holdings, cash_weight=0.2)
    assert out["long_weight"] == 0.8
    assert out["short_weight"] == 0.0
    assert out["gross_exposure"] == 0.8
    assert out["net_exposure"] == 0.8
    assert out["cash_weight"] == 0.2


def test_exposure_long_short():
    svc = RiskMetricsService(db=None)  # type: ignore[arg-type]
    holdings = {
        "a1": {"current_weight": 0.7},
        "a2": {"current_weight": -0.3},
    }
    out = svc._exposure(holdings, cash_weight=0.6)
    assert out["long_weight"] == 0.7
    assert out["short_weight"] == 0.3
    assert out["gross_exposure"] == pytest.approx(1.0)
    assert out["net_exposure"] == pytest.approx(0.4)


@pytest.mark.asyncio
async def test_risk_current_endpoint_returns_null_when_no_portfolio(client):
    r = await client.get("/api/v1/risk/current")
    assert r.status_code == 200
    body = r.json()
    # When there's no paper portfolio yet, data is null (not an error).
    assert "data" in body
    # The shape allows null; either way the response is well-formed.
    assert body["data"] is None or "portfolio_id" in body["data"]


@pytest.mark.asyncio
async def test_risk_portfolio_endpoint_404_for_unknown(client):
    r = await client.get("/api/v1/risk/portfolios/does-not-exist")
    assert r.status_code == 404
