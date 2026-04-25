# Phase 7A: RL Environment Readiness Audit

**Date:** 2026-04-25

---

## Data Availability

| Domain | Status | Detail |
|---|---|---|
| market_bars | PASS | 90 days OHLCV for 10 assets, real from local adapter |
| feature_values | PASS | 8 feature keys per asset, computed from market_bars + news |
| signal_outputs | PASS | 3 deterministic engines + 1 ML shadow, per-asset scores |
| model_predictions | PASS | ML baseline predictions (shadow), per-asset |
| backtest_runner | PASS | Walk-forward with real pipeline, weekly/monthly rebalance |
| replay_snapshots | PASS | Stage-level snapshots for pipeline recommendations |
| paper_performance | PASS | Valuation, trades, attribution from market_bars prices |
| policy_rules | PASS | 10 rules, editable, audited; position_cap=0.15, cash_floor=0.05 |
| universe_readiness | PASS | 10 assets, coverage by bars/features/signals/predictions |
| integration_health | PASS | Real local adapters, placeholder feeds labeled truthfully |
| ML shadow governance | PASS | ml_shadow_only enforced, live_pipeline_influence=false |

## What Is Ready for Offline RL

- **State construction:** market_bars + feature_values + signal_outputs + universe membership + policy constraints — all available per as_of_date
- **Action space:** target weights per asset in universe, constrained by policy rules
- **Reward computation:** portfolio return from market_bars close prices, drawdown/turnover penalties
- **Simulation loop:** rebalance dates, price lookup, portfolio value tracking — same pattern as BacktestService
- **Policy/constraint validation:** position_cap_max, cash_floor, max_invested from policy_rules table

## What Must Remain Shadow/Offline

- RL environment runs are offline simulation only
- RL does not produce recommendations consumed by pipeline
- RL does not publish anything
- RL does not influence /recommendations/current or /overview
- RL status is shadow-only in ops

## Data Limitations

- 90 days of daily bars — short for meaningful RL training (future phases need more data)
- 10 assets only — small universe
- No intraday data
- No transaction cost model beyond flat bps
- No dividends/splits
- Feature set is point-in-time but limited depth

## Design Surfaces for RL Observability

- Admin/Ops page: can add RL Environment card (same pattern as ML Observability)
- Backtests page: RL simulation runs could be listed alongside backtest experiments

## Summary

All prerequisites are met for offline RL environment construction. No blockers.
