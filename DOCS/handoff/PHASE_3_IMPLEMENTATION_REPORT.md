# Phase 3 Implementation Report

**Date:** 2026-04-24
**Phase:** Replay + Backtests + Paper Portfolio Foundation
**Status:** Complete

---

## What Was Built

### A. Replay Page (`/replay`)
- Replay list showing available recommendation replays
- Clickable replay cards that load full detail
- Replay detail: captured timestamp, rationale, confidence triplet, warnings
- Positions table at snapshot (reuses WeightsTable with right pane)
- 5 pipeline stage snapshot cards showing key-value data with timestamps

### B. Backtests Page (`/backtests`)
- Experiment list with name, date range, return, status, promotion badge
- Clickable experiment cards
- 7 result metric cards (total return, annualized, max drawdown, Sharpe, volatility, trades, turnover)
- Equity curve line chart (Recharts LineChart, base 100)
- Configuration table showing experiment parameters
- Warnings block for backtest caveats

### C. Paper Portfolio Page (`/paper`)
- Portfolio header with name and active status
- 4 summary cards: invested weight, cash, rebalances, max drift
- Drift bar chart (positive green, negative red, zero gray)
- Holdings table with target/current/drift columns (clickable, opens right pane)
- Drift threshold warning in pane for positions exceeding 1%
- Warnings block for portfolio-level alerts
- Event log with typed badges (creation, rebalance, drift_alert)

### D. Backend Expansion

**New endpoints (5):**

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/replay` | List recommendation replays |
| GET | `/api/v1/replay/{recommendation_id}` | Full replay with stages and weights |
| GET | `/api/v1/backtests` | List backtest experiments |
| GET | `/api/v1/backtests/{id}` | Backtest detail with results and equity curve |
| GET | `/api/v1/paper/current` | Active paper portfolio with holdings and events |

Total API endpoints: 12 (was 7)

### E. New Schemas

| Schema | File | Purpose |
|---|---|---|
| `ReplayDetail` | `schemas/replay.py` | Full replay with stages, weights, confidence |
| `ReplayListItem` / `ReplayListResponse` | `schemas/replay.py` | Replay listing |
| `ReplayStageSnapshot` | `schemas/replay.py` | Per-stage snapshot data |
| `BacktestDetail` | `schemas/backtest.py` | Full experiment with results and equity curve |
| `BacktestResultSummary` | `schemas/backtest.py` | Return, drawdown, Sharpe, etc. |
| `EquityCurvePoint` | `schemas/backtest.py` | Date/value pair for chart |
| `BacktestListItem` / `BacktestListResponse` | `schemas/backtest.py` | Experiment listing |
| `PaperPortfolioDetail` | `schemas/paper.py` | Portfolio with holdings, events, warnings |
| `PaperHolding` | `schemas/paper.py` | Per-asset target/current/drift |
| `PaperEvent` | `schemas/paper.py` | Timestamped portfolio event |

### F. Seed Expansion

Added to seed script:
- 5 replay snapshots (one per pipeline stage) linked to existing recommendation
- 1 backtest experiment ("Momentum Tilt v1 — 12-Month Walk-Forward") with:
  - Completed status, config, 13-point equity curve, result summary
  - Deterministic random (seed=42)
- 1 paper portfolio ("Live Shadow — Momentum Tilt v1") with:
  - 10 holdings with deterministic drift
  - 3 events (creation, rebalance, drift_alert)

### G. New Charts

| Chart | File | Used In |
|---|---|---|
| `EquityCurveChart` | `charts/EquityCurveChart.tsx` | Backtests |
| `DriftBarChart` | `charts/DriftBarChart.tsx` | Paper Portfolio |

Total chart components: 4 (was 2)

---

## What Pages Are Now Real

| Page | Status |
|---|---|
| `/` (Overview) | Real |
| `/decision` | Real |
| `/comparison` | Real |
| `/replay` | **Real** (new) |
| `/backtests` | **Real** (new) |
| `/paper` | **Real** (new) |
| `/admin` | Placeholder |

6 of 7 navigation pages are now real, data-driven pages.

---

## What Remains Placeholder
- Admin / Ops page (planned for Phase 4)
- Real ML/RL/NLP engines
- Auth / RBAC
- Production deployment
- Multiple backtest experiments
- Paper portfolio rebalance actions
- Replay comparison (side-by-side two snapshots)

---

## Files Created (12)

```
# Backend
backend/app/schemas/replay.py
backend/app/schemas/backtest.py
backend/app/schemas/paper.py
backend/app/api/v1/replay.py
backend/app/api/v1/backtests.py
backend/app/api/v1/paper.py
backend/tests/test_phase3.py

# Frontend
frontend/src/components/charts/EquityCurveChart.tsx
frontend/src/components/charts/DriftBarChart.tsx

# Docs
DOCS/handoff/PHASE_3_IMPLEMENTATION_REPORT.md
DOCS/handoff/PHASE_3_RUNBOOK.md
```

## Files Modified (7)

```
backend/app/api/router.py                — added replay, backtests, paper routes
backend/app/schemas/__init__.py          — added new schema exports
backend/seed.py                          — added replay snapshots, backtest, paper portfolio
frontend/src/services/api.ts             — added all Phase 3 types and fetch functions
frontend/src/app/replay/page.tsx         — replaced placeholder with real page
frontend/src/app/backtests/page.tsx      — replaced placeholder with real page
frontend/src/app/paper/page.tsx          — replaced placeholder with real page
```

---

## Verification Evidence

| Check | Result |
|---|---|
| Backend starts | **PASS** — 16 routes registered |
| Frontend builds | **PASS** — 7 routes, 0 errors |
| All 13 tests pass | **PASS** |
| Overview still works | **PASS** |
| Decision still works | **PASS** |
| Comparison still works | **PASS** |
| Replay endpoint | **PASS** — 1 replay, 5 stages, 10 weights |
| Backtests endpoint | **PASS** — 1 experiment, Sharpe 1.12, 13-point curve |
| Paper endpoint | **PASS** — 10 holdings, 1 drift warning |
| Seed deterministic | **PASS** — random.seed(42) |
| No regressions | **PASS** — all 8 pre-existing tests pass |

### Visual Verification

| Page | Compile | API Data | Browser Confirmed |
|---|---|---|---|
| Replay | **PASS** (1.64 kB) | **PASS** | Not confirmed |
| Backtests | **PASS** (7.83 kB) | **PASS** | Not confirmed |
| Paper | **PASS** (3.73 kB) | **PASS** | Not confirmed |

**Honest statement:** No browser rendering was confirmed during this session. All pages compile, all API paths return correct data, but visual rendering requires manual browser verification.

---

## Known Risks / Limitations

1. **Replay stage snapshots store raw JSON** — displayed as key-value pairs, not structured stage components. Sufficient for forensics but not as polished as the Decision page stage cards.
2. **Backtest equity curve uses simplified monthly data** — 13 points from deterministic random walk. Real backtests would have daily granularity.
3. **Paper portfolio events are partially hardcoded** — events are constructed from portfolio metadata since the PaperPortfolio model doesn't have a dedicated events column. The seed data supplies events through the holdings JSON structure.
4. **Single backtest / single paper portfolio** — only one of each exists in seed. Multi-experiment and multi-portfolio selection is structurally supported but untested with multiple items.
5. **No Alembic migration needed** — all new data uses existing tables (replay_snapshots, backtest_experiments, paper_portfolios) that were created in migration 001.
