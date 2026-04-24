# Phase 3 Runbook

**Updated:** 2026-04-24

## Startup

Same as previous phases. No new infrastructure required.

### Quick start
```bash
# Terminal 1: Backend
cd backend
pip install -r requirements.txt
rm -f finrlx_dev.db        # fresh start recommended for Phase 3 seed
alembic upgrade head
python -m seed
uvicorn app.main:app --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

### Run tests
```bash
cd backend
python -m pytest tests/ -v
# Expected: 13 passed
```

---

## URLs to Verify

| Page / Endpoint | URL |
|---|---|
| Overview | http://localhost:3000 |
| Decision Workspace | http://localhost:3000/decision |
| Comparison | http://localhost:3000/comparison |
| **Replay** | http://localhost:3000/replay |
| **Backtests** | http://localhost:3000/backtests |
| **Paper Portfolio** | http://localhost:3000/paper |
| Admin (placeholder) | http://localhost:3000/admin |
| API: Replay list | http://localhost:8000/api/v1/replay |
| API: Backtests list | http://localhost:8000/api/v1/backtests |
| API: Paper current | http://localhost:8000/api/v1/paper/current |
| Swagger | http://localhost:8000/docs |

---

## What to Click / Expected Outcomes

### Replay (/replay)
- Page heading: "Replay / Forensics"
- Shows 1 available replay with recommendation ID, position count, status badge
- Clicking the replay card loads full detail below:
  - Replay header with captured timestamp and data-as-of
  - Rationale at snapshot
  - Trust/confidence bars (78% / 92% / 95%)
  - Warnings block (NVDA cap)
  - Positions table (10 rows, clickable to open right pane)
  - Pipeline Stage Snapshots: 5 cards (selection, allocation, timing, risk_overlay, publication)
  - Each stage card shows key-value snapshot data with timestamps

### Backtests (/backtests)
- Page heading: "Backtests", 1 experiment
- Experiment card: "Momentum Tilt v1 — 12-Month Walk-Forward"
  - Date range shown
  - Total return percentage shown (green if positive)
  - "completed" status badge
- Clicking loads detail:
  - 7 metric cards: Total Return, Annualized Return, Max Drawdown, Sharpe (1.12), Volatility, Total Trades (48), Avg Turnover
  - Equity curve line chart (base 100, ~13 monthly points)
  - Configuration table: strategy, rebalance_frequency, universe, benchmark, cost_model, etc.
  - 2 warnings about simplified cost model and limited window

### Paper Portfolio (/paper)
- Page heading: "Paper Portfolio"
- Portfolio name: "Live Shadow — Momentum Tilt v1"
- "published" status badge (active)
- 4 summary cards: Invested (~100%), Cash (0%), Rebalances (1), Max Drift
- Drift chart: bar chart showing per-position drift from target (green positive, red negative)
- Holdings table: 10 rows with target, current, drift columns
  - "Click a row to inspect" hint
  - Clicking opens right pane with target/current/drift detail
  - Positions exceeding 1% drift show amber warning in pane
- Warnings block: drift alert for positions exceeding threshold
- Event log: 2-3 events (creation, rebalance, drift_alert) with timestamps and type badges

---

## Seed Data Summary

Phase 3 seed adds to existing data:
- **5 replay snapshots** (one per pipeline stage: selection, allocation, timing, risk_overlay, publication)
- **1 backtest experiment** ("Momentum Tilt v1") with completed results, equity curve, and config
- **1 paper portfolio** ("Live Shadow") with 10 drifted holdings and 3 events

Seed output: `Seeded: 10 assets, 1 universe, 1 recommendation, 5 replay snapshots, 1 backtest, 1 paper portfolio`

---

## Troubleshooting

**Replay page shows "No Replay Data":**
- Re-seed: `rm -f finrlx_dev.db && alembic upgrade head && python -m seed`
- Phase 3 seed creates replay snapshots that Phase 0+1 seed did not

**Backtests equity curve is empty:**
- Ensure you re-seeded (old seed didn't include backtest data)

**Paper drift values seem random:**
- Drift is generated deterministically (random.seed(42)) but with small random perturbations around target weights
