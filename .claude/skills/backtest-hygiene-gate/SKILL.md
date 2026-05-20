---
name: backtest-hygiene-gate
description: CI gate that fails on common quantitative-backtest pathologies — look-ahead bias, missing out-of-sample split, Sharpe>3 without explicit override, insufficient rebalance count, and oversized per-period returns. Run on every BacktestExperiment that lands in the database and on any change to `app/services/backtesting.py`.
type: project
---

# Backtest Hygiene Gate

A FINRLX-internal validator that protects the product from publishing backtest results that overstate model quality. Cheap, fast, and run in CI on every PR that touches the backtesting code.

## Why this matters

Most "great" backtest numbers are wrong because of one of five mistakes:

1. **Look-ahead bias** — the strategy decided at date T using data that was not actually available until after T.
2. **No out-of-sample split** — the strategy was tuned on the same data it was scored on.
3. **Cherry-picked period** — the backtest covers exactly the window where the strategy happens to work.
4. **Sharpe inflation** — sample-size or autocorrelation artifacts pushing Sharpe above what a real strategy could deliver.
5. **Per-period outliers** — one or two rebalances did all the work; the strategy did nothing the rest of the time.

This skill encodes those five into a hard CI gate. Each rule maps to one of `app/services/backtest_hygiene.py`'s checks.

## Rules

| Rule | Threshold | Override | Severity |
|---|---|---|---|
| `requires_walk_forward` | `config.methodology` must equal `"walk-forward"` | none | BLOCK |
| `min_rebalance_count` | At least 3 rebalance points (rebalance_dates length >= 3) | none | BLOCK |
| `rebalance_dates_in_order` | `rebalance_dates` strictly increasing | none | BLOCK |
| `no_lookahead_data_as_of` | For each decision_point at date T, the linked Recommendation's `data_as_of` must satisfy `data_as_of <= T` | none | BLOCK |
| `sharpe_in_range` | `sharpe_ratio` must be ≤ 3.0 | `config.allow_high_sharpe_override = true` with `override_reason` non-empty | BLOCK without override |
| `max_per_period_return` | No single period's return > 50% in absolute value | `config.allow_outlier_returns = true` | WARN |
| `min_period_count_for_metrics` | If `sharpe_ratio` or `volatility` is reported, at least 6 period returns must exist | none | BLOCK |
| `equity_curve_internally_consistent` | First equity point = 100.0, last point ≈ 100 * (1 + total_return) within 0.05% tolerance | none | BLOCK |

A `BLOCK` rule failing means the experiment must be marked `status="failed"` and `results_summary.warnings` must explicitly include the rule name. A `WARN` rule failing means a warning is appended but the experiment can still complete.

## How to apply

When invoked on:

- a `BacktestExperiment` row → call `BacktestHygieneGate.evaluate(experiment)` (returns `HygieneReport` with `passed: bool`, `block_violations: list[str]`, `warn_violations: list[str]`).
- a code change touching `app/services/backtesting.py` → confirm `pytest backend/tests/test_mvp6_backtest_hygiene.py` is still green.

For Sharpe-override usage: an operator who needs to publish a high-Sharpe result must set both:

```python
bt.config["allow_high_sharpe_override"] = True
bt.config["override_reason"] = "Statistical justification documented in <doc/url>"
```

If `override_reason` is empty or missing, the override is treated as absent.

## What this skill does NOT do

- Does not run statistical tests (DM test, White's reality check, deflated Sharpe). That's MVP-7+ scope.
- Does not check for trading-cost realism. The cost model is configured at `cost_bps` and not second-guessed.
- Does not enforce universe stability — a universe that gains/loses tickers mid-backtest is a real failure mode but not in scope here.
- Does not look at slippage assumptions.

## Reference

- "Backtest Overfitting and Out-of-Sample Performance" — Bailey, Borwein, López de Prado, Zhu (2014).
- "Pseudo-Mathematics and Financial Charlatanism" — López de Prado (2014).
- The skill is intentionally narrow: a CI tripwire, not a full validation suite.
