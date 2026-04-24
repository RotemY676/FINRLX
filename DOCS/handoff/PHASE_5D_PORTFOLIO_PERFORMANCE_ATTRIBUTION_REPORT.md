# Phase 5D: Portfolio Performance & Attribution — Report

**Date:** 2026-04-25
**Phase:** 5D — Time-series performance, trade ledger, attribution
**Status:** Complete

---

## 1. Files Changed

### Created (3)
```
backend/migrations/versions/009_paper_performance.py — paper_valuation_snapshots + paper_trades tables
backend/tests/test_phase5d_paper_performance.py     — 8 performance tests
DOCS/handoff/PHASE_5D_PORTFOLIO_PERFORMANCE_ATTRIBUTION_REPORT.md
```

### Modified (4)
```
backend/app/models/validation.py   — added PaperValuationSnapshot, PaperTrade models
backend/app/models/__init__.py     — registered new models
backend/app/services/paper.py      — added performance, trades, attribution methods
backend/app/schemas/paper.py       — added valuation, trade, performance, attribution schemas
backend/app/api/v1/paper.py        — added 7 performance/attribution endpoints
```

---

## 2. Tables Added (migration 009)

| Table | Key Columns |
|---|---|
| `paper_valuation_snapshots` | portfolio_id, valuation_date, portfolio_value, cash_value, invested_value, daily_return, cumulative_return, max_drawdown_to_date |
| `paper_trades` | portfolio_id, recommendation_id, trade_date, asset_id, ticker, side, quantity, price, notional, weight_delta, reason |

---

## 3. Endpoints Added (7)

| Method | Path | Purpose |
|---|---|---|
| POST | `/paper/{id}/performance/recompute` | Generate valuation snapshots + return performance |
| GET | `/paper/{id}/performance` | Performance summary (return, drawdown, Sharpe) |
| GET | `/paper/{id}/valuations` | Time-series valuation points |
| GET | `/paper/{id}/trades` | Simulated trade ledger |
| GET | `/paper/{id}/attribution/assets` | Per-asset return contribution |
| GET | `/paper/{id}/attribution/decisions` | Per-decision event history |

---

## 4. Formulas

**Daily return:** `(value_today - value_yesterday) / value_yesterday`

**Cumulative return:** `(value_today - starting_value) / starting_value`

**Max drawdown:** `max(peak - trough) / peak` over all snapshots (negative convention)

**Volatility:** `std(daily_returns) × sqrt(252)` annualized

**Sharpe:** `mean(daily_returns) × 252 / volatility`

**Asset contribution:** `asset_weight × asset_return`

---

## 5. Test Output

```
$ python -m pytest tests/ -v
166 passed, 2 skipped, 1 warning in 11.97s

  8 new Phase 5D tests
  158 existing tests — all PASS
```

---

## 6. What Is Now Real

| Component | Status |
|---|---|
| Trade ledger | **REAL** — buy trades generated from recommendation weights at market prices |
| Valuation snapshots | **REAL** — daily portfolio value from market_bars close prices |
| Performance metrics | **REAL** — return, drawdown, vol, Sharpe from actual price data |
| Asset attribution | **REAL** — per-asset contribution from entry price to current |
| Decision attribution | **REAL** — per-event history with turnover and trade count |

---

## 7. Known Limitations

1. **No broker/execution** — all trades are simulated paper fills at DB close price.
2. **No benchmark comparison yet** — returns are absolute, not relative.
3. **No dividends/splits/corporate actions** — price-only simulation.
4. **Cash earns nothing** — cash_drag tracked but no interest.
5. **Integer quantities** — fractional shares not supported.
6. **Engine attribution** not implemented — would require deeper signal-to-weight lineage.
7. **Valuation snapshots require manual recompute** — not auto-generated on price update.

---

## Phase 5D.1 Truthfulness Hardening Addendum

**Date:** 2026-04-25

### Fixes

1. **Trade backfill.** `recompute` now detects portfolios with holdings but no trades and creates backfilled initial buy trades (reason="backfilled_initial_holding"). Repeated recompute does not duplicate trades.

2. **Asset attribution fixed.** Now queries market_bars for actual start/end prices using the valuation snapshot window, not stale `last_price` from holdings JSON. Returns `quality="partial"` with `start_price`/`end_price` when data is missing.

3. **Performance basis.** Summary now includes `performance_basis`, `basis_start_date`, `basis_end_date`, and `warnings` when the measurement window differs from original starting cash.

### Tests Added (5)

| Test | What It Verifies |
|---|---|
| `test_recompute_backfills_trades` | Recompute creates trades for holdings-only portfolios |
| `test_repeated_recompute_no_duplicate_trades` | No duplicate trades on repeated recompute |
| `test_create_from_recommendation_creates_trades` | New portfolio has initial buy trades |
| `test_attribution_non_zero_with_price_data` | Attribution includes quality/start_price/end_price |
| `test_performance_includes_basis` | Performance has basis fields |

### Test Output

```
171 passed, 2 skipped, 1 warning in 12.70s
```
