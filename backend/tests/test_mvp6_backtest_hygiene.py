"""Backtest hygiene gate — unit tests for `app.services.backtest_hygiene.evaluate`.

The hygiene gate is a pure function over (config, results_summary,
decision_data_as_of). We don't need the DB or any fixtures; each test
builds the smallest payload that exercises one rule.
"""
from __future__ import annotations

import pytest

from app.services.backtest_hygiene import (
    MIN_REBALANCE_POINTS,
    SHARPE_BLOCK_THRESHOLD,
    evaluate,
)


def _ok_summary() -> dict:
    """A backtest summary that should pass every rule on its own."""
    return {
        "rebalance_dates": ["2026-01-01", "2026-02-01", "2026-03-01", "2026-04-01"],
        "decision_points": [
            {"date": "2026-02-01", "recommendation_id": "rec-1"},
            {"date": "2026-03-01", "recommendation_id": "rec-2"},
            {"date": "2026-04-01", "recommendation_id": "rec-3"},
        ],
        "sharpe_ratio": 1.2,
        "volatility": 0.18,
        "total_return": 0.08,
        "equity_curve": [
            {"date": "2026-01-01", "value": 100.0},
            {"date": "2026-04-01", "value": 108.0},
        ],
        "period_returns": [0.02, 0.03, 0.025, 0.005, 0.0, -0.005, 0.01],
    }


def _ok_config() -> dict:
    return {"methodology": "walk-forward"}


def test_clean_backtest_passes_every_rule():
    report = evaluate(config=_ok_config(), results_summary=_ok_summary())
    assert report.passed is True, report.block_violations
    assert report.block_violations == []


def test_missing_walk_forward_methodology_blocks():
    cfg = {"methodology": "buy-and-hold"}  # not walk-forward
    report = evaluate(config=cfg, results_summary=_ok_summary())
    assert report.passed is False
    assert "requires_walk_forward" in report.block_violations


def test_too_few_rebalance_points_blocks():
    summary = _ok_summary()
    summary["rebalance_dates"] = ["2026-01-01", "2026-02-01"]  # only 2, need >=3
    report = evaluate(config=_ok_config(), results_summary=summary)
    assert "min_rebalance_count" in report.block_violations
    assert report.details["rebalance_count"] == 2
    assert MIN_REBALANCE_POINTS == 3  # contract documented in skill


def test_out_of_order_rebalance_dates_blocks():
    summary = _ok_summary()
    summary["rebalance_dates"] = ["2026-03-01", "2026-01-01", "2026-02-01", "2026-04-01"]
    report = evaluate(config=_ok_config(), results_summary=summary)
    assert "rebalance_dates_in_order" in report.block_violations


def test_duplicate_rebalance_dates_blocks():
    summary = _ok_summary()
    summary["rebalance_dates"] = ["2026-01-01", "2026-02-01", "2026-02-01", "2026-04-01"]
    report = evaluate(config=_ok_config(), results_summary=summary)
    assert "rebalance_dates_in_order" in report.block_violations


def test_lookahead_data_as_of_blocks():
    # decision at 2026-02-01 used data dated 2026-02-15 — look-ahead.
    decision_data = {"rec-1": "2026-02-15"}
    report = evaluate(
        config=_ok_config(),
        results_summary=_ok_summary(),
        decision_data_as_of=decision_data,
    )
    assert "no_lookahead_data_as_of" in report.block_violations
    assert report.details["lookahead_violations"][0]["recommendation_id"] == "rec-1"


def test_lookahead_check_skipped_when_provenance_absent():
    """No provenance mapping → cannot evaluate → rule is not violated."""
    report = evaluate(
        config=_ok_config(),
        results_summary=_ok_summary(),
        decision_data_as_of=None,
    )
    assert "no_lookahead_data_as_of" not in report.block_violations


def test_decision_data_as_of_equal_to_rebalance_date_is_ok():
    """End-of-day data as of the rebalance date is acceptable, not look-ahead."""
    decision_data = {"rec-1": "2026-02-01", "rec-2": "2026-03-01"}
    report = evaluate(
        config=_ok_config(),
        results_summary=_ok_summary(),
        decision_data_as_of=decision_data,
    )
    assert "no_lookahead_data_as_of" not in report.block_violations


def test_high_sharpe_without_override_blocks():
    summary = _ok_summary()
    summary["sharpe_ratio"] = 4.2  # above threshold
    report = evaluate(config=_ok_config(), results_summary=summary)
    assert "sharpe_in_range" in report.block_violations
    assert SHARPE_BLOCK_THRESHOLD == 3.0


def test_high_sharpe_with_active_override_passes():
    summary = _ok_summary()
    summary["sharpe_ratio"] = 4.2
    cfg = {
        "methodology": "walk-forward",
        "allow_high_sharpe_override": True,
        "override_reason": "Single-asset universe; high Sharpe expected for the synthetic test fixture.",
    }
    report = evaluate(config=cfg, results_summary=summary)
    assert "sharpe_in_range" not in report.block_violations


def test_high_sharpe_with_override_flag_but_no_reason_still_blocks():
    """A flag without a documented reason is not a valid override."""
    summary = _ok_summary()
    summary["sharpe_ratio"] = 4.2
    cfg = {
        "methodology": "walk-forward",
        "allow_high_sharpe_override": True,
        # override_reason intentionally missing
    }
    report = evaluate(config=cfg, results_summary=summary)
    assert "sharpe_in_range" in report.block_violations


def test_outlier_period_return_warns_not_blocks():
    summary = _ok_summary()
    summary["period_returns"] = [0.02, 0.65, 0.01, 0.005, 0.0, 0.01, -0.005]
    # Need to recompute equity curve consistently so we don't trip another rule.
    # Just compound: total = product(1+r) - 1.
    total = 1.0
    for r in summary["period_returns"]:
        total *= (1 + r)
    summary["total_return"] = total - 1
    summary["equity_curve"] = [
        {"date": "2026-01-01", "value": 100.0},
        {"date": "2026-04-01", "value": round(100.0 * total, 4)},
    ]
    report = evaluate(config=_ok_config(), results_summary=summary)
    assert "max_per_period_return" in report.warn_violations
    # Outlier alone shouldn't fail the gate.
    assert report.passed is True


def test_too_few_period_returns_for_sharpe_blocks():
    summary = _ok_summary()
    summary["period_returns"] = [0.01, 0.02]  # only 2, need >= 6
    summary["rebalance_dates"] = ["2026-01-01", "2026-02-01", "2026-03-01"]
    report = evaluate(config=_ok_config(), results_summary=summary)
    assert "min_period_count_for_metrics" in report.block_violations


def test_equity_curve_must_start_at_100():
    summary = _ok_summary()
    summary["equity_curve"] = [
        {"date": "2026-01-01", "value": 95.0},  # not 100
        {"date": "2026-04-01", "value": 108.0},
    ]
    report = evaluate(config=_ok_config(), results_summary=summary)
    assert "equity_curve_internally_consistent" in report.block_violations


def test_equity_curve_end_must_match_total_return():
    summary = _ok_summary()
    summary["equity_curve"] = [
        {"date": "2026-01-01", "value": 100.0},
        {"date": "2026-04-01", "value": 200.0},  # doesn't match total_return=0.08
    ]
    report = evaluate(config=_ok_config(), results_summary=summary)
    assert "equity_curve_internally_consistent" in report.block_violations


def test_empty_inputs_dont_crash():
    """Defensive — a totally empty payload should report violations, not crash."""
    report = evaluate(config=None, results_summary=None)
    assert report.passed is False
    # No methodology → walk-forward rule fails. No rebalance dates → count fails.
    assert "requires_walk_forward" in report.block_violations
    assert "min_rebalance_count" in report.block_violations
