"""Phase 19A.1 — Calmar ratio computation.

Calmar = annualized_return / |max_drawdown|.

`max_drawdown` is stored signed-negative across the service (e.g. -0.21 for a
21% drawdown). The pure helper accepts that convention.
"""
from __future__ import annotations

import pytest

from app.services.backtesting import _calc_calmar


def test_calmar_simple_positive_case():
    # 15% annualized return, 10% drawdown → Calmar = 1.5
    assert _calc_calmar(0.15, -0.10) == 1.5


def test_calmar_negative_annualized_return():
    # Underperforming strategy: returns negative Calmar.
    assert _calc_calmar(-0.05, -0.20) == -0.25


def test_calmar_absorbs_dd_sign_either_way():
    # Whether max_drawdown is stored positive or negative, denominator is |dd|.
    assert _calc_calmar(0.20, -0.10) == _calc_calmar(0.20, 0.10) == 2.0


def test_calmar_zero_drawdown_returns_none():
    # Undefined ratio; we choose None over +inf so downstream serializers stay clean.
    assert _calc_calmar(0.10, 0.0) is None


def test_calmar_none_inputs_return_none():
    assert _calc_calmar(None, -0.10) is None
    assert _calc_calmar(0.10, None) is None
    assert _calc_calmar(None, None) is None


def test_calmar_rounded_to_two_decimals():
    # 0.1234 / 0.0500 = 2.468 → rounded to 2.47
    assert _calc_calmar(0.1234, -0.0500) == 2.47


def test_results_summary_includes_calmar_for_a_completed_backtest(monkeypatch):
    """Smoke: when the service writes the summary it includes calmar_ratio.

    We don't run a real backtest here — that requires the full DB + fixtures
    and is covered by the integration suite. Instead we verify the dict shape
    by inspecting the literal source for the key (cheap guard against the
    field being dropped accidentally during a refactor).
    """
    from pathlib import Path

    src = (Path(__file__).resolve().parents[1] / "app" / "services" / "backtesting.py").read_text()
    assert '"calmar_ratio": calmar' in src, "results_summary lost calmar_ratio"


def test_schema_has_calmar_ratio_field():
    """Pydantic schema mirrors the service output."""
    from app.schemas.backtest import BacktestResultSummary

    fields = BacktestResultSummary.model_fields
    assert "calmar_ratio" in fields
    # Default is None so a backtest that hasn't been re-run is still valid.
    assert fields["calmar_ratio"].default is None
