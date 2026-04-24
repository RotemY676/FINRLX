# Phase 5C: Paper Portfolio Realization — Report

**Date:** 2026-04-24
**Phase:** 5C — Paper Portfolio driven by published recommendations
**Status:** Complete

---

## 1. Files Changed

### Created (4)
```
backend/app/services/paper.py                   — PaperPortfolioService
backend/migrations/versions/008_paper_provenance.py — portfolio_value, source_recommendation_id, source_type, events_log
backend/tests/test_phase5c_paper.py             — 8 paper portfolio tests
DOCS/handoff/PHASE_5C_PAPER_PORTFOLIO_REPORT.md
```

### Modified (3)
```
backend/app/models/validation.py   — added provenance fields to PaperPortfolio model
backend/app/schemas/paper.py       — added source_type, is_demo, lineage_available, portfolio_value, drift schema
backend/app/api/v1/paper.py        — rewritten: 7 endpoints with provenance + create/rebalance/drift/events
```

---

## 2. Tables Modified (migration 008)

| Column | Type | Purpose |
|---|---|---|
| `portfolio_value` | Float | Current total portfolio value |
| `source_recommendation_id` | String(36) | Which recommendation created this portfolio |
| `source_type` | String(30) | "recommendation_paper", "seed_demo", "test_paper", "unknown" |
| `events_log` | JSON | Event history (creation, rebalance, drift alerts) |

---

## 3. Endpoints (7)

| Method | Path | Purpose |
|---|---|---|
| GET | `/paper/current` | Active paper portfolio with provenance |
| GET | `/paper` | List all portfolios |
| GET | `/paper/{id}` | Single portfolio detail |
| POST | `/paper/from-recommendation/{rec_id}` | Create from published recommendation |
| POST | `/paper/{id}/rebalance/{rec_id}` | Rebalance from new recommendation |
| GET | `/paper/{id}/drift` | Compute drift from latest market prices |
| GET | `/paper/{id}/events` | Event log |

---

## 4. Paper Simulation Methodology

**Creation:** Allocate `starting_value` (default 100,000) according to recommendation weights. Use latest `market_bars` close price per asset. Compute `quantity = target_value / close_price`.

**Drift:** Recompute `current_value = quantity × latest_close`. Recompute `current_weight = current_value / total_portfolio_value`. `drift = current_weight - target_weight`.

**Rebalance:** Update target weights from new recommendation. Compute simulated trades and turnover. No real execution.

---

## 5. Provenance Rules

| Source | source_type | is_demo | Allowed |
|---|---|---|---|
| Published recommendation | `recommendation_paper` | false | Default |
| Draft with `allow_unpublished=true` | `test_paper` | false | Testing only |
| Draft without flag | — | — | Rejected (400) |
| Seeded portfolio | `seed_demo` / `unknown` | true | Legacy only |

---

## 6. Test Output

```
$ python -m pytest tests/ -v
157 passed, 1 skipped, 1 warning in 11.83s

  8 new Phase 5C tests
  150 existing tests — all PASS (zero regressions)
  1 skipped: publish blocked by test DB incidents/breaches (correct governance)
```

---

## 7. What Is Now Real

| Component | Status |
|---|---|
| Paper portfolio creation | **REAL** — from published recommendation weights + market_bars prices |
| Holdings | **REAL** — target_weight, current_weight, quantity, price from DB |
| Drift | **REAL** — computed from latest market_bars close prices |
| Rebalance | **REAL** — updates holdings from new recommendation |
| Events | **REAL** — creation/rebalance events with metadata |
| Provenance | **REAL** — source_recommendation_id, source_type classification |

---

## 8. Known Limitations

1. **No real broker/execution** — all fills are simulated paper fills.
2. **No P&L tracking over time** — only point-in-time drift, not historical P&L curve.
3. **No dividends/splits** — price-only simulation.
4. **Cash is not invested** — cash_weight is tracked but not earning interest.
5. **Quantity is integer** — fractional shares not supported.
6. **Single active portfolio** — creating a new one deactivates the previous.
