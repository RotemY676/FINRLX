"""Backtest hygiene gate.

A small, pure-function validator that scans a `BacktestExperiment`'s config
and results_summary against the rules in `.claude/skills/backtest-hygiene-gate`.

Pure-function design — no DB access, no I/O — so it's trivial to call from a
service, a CI test, or a CLI tool.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

# Block-severity threshold for sharpe; values above need an explicit override.
SHARPE_BLOCK_THRESHOLD = 3.0
# Warn-severity threshold for any single rebalance's period return (absolute).
PER_PERIOD_RETURN_WARN_THRESHOLD = 0.50
# Minimum rebalance points for a backtest to be considered structurally valid.
MIN_REBALANCE_POINTS = 3
# Minimum period returns required before Sharpe/vol are statistically meaningful.
MIN_PERIODS_FOR_METRICS = 6
# Tolerance for end-of-curve consistency check (5 bps).
EQUITY_CURVE_TOLERANCE = 0.0005


@dataclass
class HygieneReport:
    """Result of evaluating a backtest against the hygiene gate."""

    passed: bool
    block_violations: list[str] = field(default_factory=list)
    warn_violations: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


def _parse_iso_date(value: Any) -> date | None:
    """Best-effort parse of an ISO-format date/datetime into a date.

    Returns None if the value can't be coerced — caller decides what to do.
    """
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return None
    return None


def _override_active(config: dict[str, Any], flag: str) -> bool:
    """An override counts only if its boolean flag AND a reason are both set."""
    if not config.get(flag):
        return False
    reason = config.get("override_reason")
    return isinstance(reason, str) and reason.strip() != ""


def evaluate(
    *,
    config: dict[str, Any] | None,
    results_summary: dict[str, Any] | None,
    decision_data_as_of: dict[str, date | datetime | str] | None = None,
) -> HygieneReport:
    """Run every hygiene rule against a backtest experiment's payload.

    Parameters
    ----------
    config:
        The `BacktestExperiment.config` dict. Must contain `methodology`. May
        contain `allow_high_sharpe_override` + `override_reason` for the
        Sharpe rule, or `allow_outlier_returns` for per-period returns.
    results_summary:
        The `BacktestExperiment.results_summary` dict produced by
        `BacktestService.run_backtest`. We read `rebalance_dates`,
        `decision_points`, `sharpe_ratio`, `volatility`, `equity_curve`,
        `total_return`, and (optionally) per-period returns under a future
        `period_returns` key. Tolerant of missing fields — missing data is
        an empty list, not a violation by itself, except for blocks below.
    decision_data_as_of:
        Optional mapping `{recommendation_id -> data_as_of}` used to check
        look-ahead. If omitted, the look-ahead rule is skipped (the rule
        cannot evaluate without provenance).
    """
    config = config or {}
    summary = results_summary or {}
    blocks: list[str] = []
    warns: list[str] = []
    details: dict[str, Any] = {}

    # Rule: walk-forward methodology must be declared
    if config.get("methodology") != "walk-forward":
        blocks.append("requires_walk_forward")

    # Rule: at least MIN_REBALANCE_POINTS rebalance points
    rebalance_dates_raw = summary.get("rebalance_dates") or []
    rebalance_dates = [_parse_iso_date(d) for d in rebalance_dates_raw]
    rebalance_dates_clean = [d for d in rebalance_dates if d is not None]
    details["rebalance_count"] = len(rebalance_dates_clean)
    if len(rebalance_dates_clean) < MIN_REBALANCE_POINTS:
        blocks.append("min_rebalance_count")

    # Rule: rebalance dates strictly increasing
    if rebalance_dates_clean and rebalance_dates_clean != sorted(rebalance_dates_clean):
        blocks.append("rebalance_dates_in_order")
    elif len(rebalance_dates_clean) >= 2:
        # Strict (no duplicates)
        if len(set(rebalance_dates_clean)) != len(rebalance_dates_clean):
            blocks.append("rebalance_dates_in_order")

    # Rule: no look-ahead. For each decision point we know the rebalance date
    # and the recommendation id; we cross-check against the supplied mapping.
    if decision_data_as_of:
        for dp in summary.get("decision_points") or []:
            rid = dp.get("recommendation_id")
            d = _parse_iso_date(dp.get("date"))
            if rid is None or d is None:
                continue
            data_as_of = decision_data_as_of.get(rid)
            if data_as_of is None:
                continue
            data_as_of_d = _parse_iso_date(data_as_of)
            if data_as_of_d is not None and data_as_of_d > d:
                blocks.append("no_lookahead_data_as_of")
                details.setdefault("lookahead_violations", []).append(
                    {"recommendation_id": rid, "decision_date": d.isoformat(),
                     "data_as_of": data_as_of_d.isoformat()}
                )
                break  # one violation is enough to fail

    # Rule: Sharpe in range (with optional override)
    sharpe = summary.get("sharpe_ratio")
    if isinstance(sharpe, int | float) and sharpe > SHARPE_BLOCK_THRESHOLD:
        if not _override_active(config, "allow_high_sharpe_override"):
            blocks.append("sharpe_in_range")
            details["sharpe_ratio"] = sharpe

    # Rule: enough periods to justify Sharpe/vol
    period_returns = summary.get("period_returns") or []
    if (sharpe is not None or summary.get("volatility") is not None) \
            and len(period_returns) < MIN_PERIODS_FOR_METRICS:
        # Best-effort: if period_returns isn't reported, infer from rebalance_count - 1
        inferred = max(len(rebalance_dates_clean) - 1, 0)
        if inferred < MIN_PERIODS_FOR_METRICS:
            blocks.append("min_period_count_for_metrics")
            details["effective_periods"] = inferred

    # Rule: max per-period return (WARN)
    outliers = [r for r in period_returns if isinstance(r, int | float) and abs(r) > PER_PERIOD_RETURN_WARN_THRESHOLD]
    if outliers and not config.get("allow_outlier_returns"):
        warns.append("max_per_period_return")
        details["outlier_period_returns"] = outliers

    # Rule: equity curve consistency
    curve = summary.get("equity_curve") or []
    total_return = summary.get("total_return")
    if curve and isinstance(total_return, int | float):
        try:
            first = float(curve[0].get("value"))
            last = float(curve[-1].get("value"))
        except (AttributeError, TypeError, ValueError):
            blocks.append("equity_curve_internally_consistent")
        else:
            if abs(first - 100.0) > 1e-6:
                blocks.append("equity_curve_internally_consistent")
            else:
                expected_last = 100.0 * (1 + total_return)
                if expected_last == 0:
                    if abs(last) > EQUITY_CURVE_TOLERANCE:
                        blocks.append("equity_curve_internally_consistent")
                elif abs(last - expected_last) / max(abs(expected_last), 1e-9) > EQUITY_CURVE_TOLERANCE:
                    blocks.append("equity_curve_internally_consistent")

    return HygieneReport(
        passed=(len(blocks) == 0),
        block_violations=sorted(set(blocks)),
        warn_violations=sorted(set(warns)),
        details=details,
    )


__all__ = ["evaluate", "HygieneReport"]
