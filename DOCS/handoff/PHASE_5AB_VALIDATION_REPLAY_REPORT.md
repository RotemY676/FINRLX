# Phase 5A+B: Validation & Replay Realization — Report

**Date:** 2026-04-24
**Phase:** 5A+B — Backtest Runner + Replay Realization
**Status:** Complete

---

## 1. Files Changed

### Created (4)
```
backend/app/services/backtesting.py        — BacktestService: walk-forward simulation
backend/app/services/replay.py             — ReplayService: snapshot capture for pipeline recs
backend/tests/test_phase5ab_validation_replay.py — 12 validation + replay tests
DOCS/handoff/PHASE_5AB_VALIDATION_REPLAY_REPORT.md
```

### Modified (4)
```
backend/app/schemas/backtest.py   — added BacktestRunRequest, BacktestStatusResponse
backend/app/api/v1/backtests.py   — added POST /backtests/run, GET /backtests/status
backend/app/api/v1/replay.py      — auto-create replay for pipeline recs, seeded-data warning
backend/seed.py                    — create replay snapshots for pipeline recommendation
```

---

## 2. Tables Reused (no migration)

All existing tables sufficient: `backtest_experiments`, `replay_snapshots`, `recommendations`, `recommendation_weights`, `selection_runs`, `allocation_results`, `timing_results`, `risk_overlay_results`, `market_bars`, `feature_sets`, `signal_runs`.

---

## 3. Backtest Methodology

**Walk-forward simulation:**
1. Generate rebalance dates (weekly or monthly) from start to end
2. At each rebalance: compute features → run engines → run pipeline → get weights
3. Between rebalances: compute portfolio return from actual market_bar close prices
4. Apply transaction cost (fixed bps) at each rebalance
5. Track equity curve, drawdown, returns

**Metrics computed:**
- `total_return = (final_value - 100) / 100`
- `annualized_return = (1 + total_return)^(365/days) - 1`
- `max_drawdown = max(peak - trough) / peak` (negative convention)
- `volatility = std(period_returns) * sqrt(periods_per_year)`
- `sharpe_ratio = mean(period_returns) * periods_per_year / volatility`
- `turnover = sum(|weight_changes|) per rebalance`
- `win_rate = count(positive_periods) / total_periods`

**Lookahead avoidance:** Features query `bar_date <= as_of`, so no future data is used. Each rebalance computes features as-of the rebalance date.

---

## 4. Replay Methodology

- `ReplayService.create_replay_for_recommendation()` captures all pipeline stages as snapshots
- Stages captured: selection, allocation, timing, risk_overlay, recommendation (with lineage)
- Replay list endpoint auto-creates snapshots for pipeline recs that lack them
- Replay detail includes `source_feature_set_id` and `source_signal_run_ids` in the recommendation stage
- Seeded (non-pipeline) replays are labeled with a warning: "This replay is from seeded/demo data"

---

## 5. Endpoints Added/Modified

| Method | Path | Change |
|---|---|---|
| POST | `/backtests/run` | **NEW** — trigger walk-forward backtest |
| GET | `/backtests/status` | **NEW** — backtest layer status |
| GET | `/backtests` | Unchanged (lists all experiments) |
| GET | `/backtests/{id}` | Unchanged (single experiment detail) |
| GET | `/replay` | **MODIFIED** — auto-creates replay for pipeline recs |
| GET | `/replay/{id}` | **MODIFIED** — auto-creates, warns on seeded data |

---

## 6. Test Output

```
$ python -m pytest tests/ -v
142 passed, 1 warning in 9.12s

  12 new Phase 5A+B tests
  130 existing tests — all PASS (zero regressions)
```

---

## 7. What Is Now Real

| Component | Status |
|---|---|
| Backtest runner | **REAL** — walk-forward using market_bars + pipeline logic |
| Equity curve | **REAL** — computed from actual close prices |
| Metrics | **REAL** — total return, drawdown, Sharpe from real data |
| Replay snapshots | **REAL** — captured from pipeline stage records |
| Replay lineage | **REAL** — links back to feature_set + signal_runs |

---

## 8. Known Limitations

1. **Backtest is expensive** — each rebalance runs features + engines + pipeline. Not suitable for 10+ year backtests yet.
2. **No benchmark comparison** — backtest returns are absolute, not relative to SPY/equal-weight.
3. **No walk-forward holdout** — all data is used, no train/test split.
4. **Seed does not auto-run backtest** — too expensive. Must call `POST /backtests/run` manually.
5. **Replay is point-in-time** — no temporal replay scrubber or animation.
6. **Paper portfolio** not yet realized — still uses old seeded data.
