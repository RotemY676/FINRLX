# Design Sprint 2 Runbook

**Updated:** 2026-04-24

## Startup

```bash
# Terminal 1: Backend
cd backend
pip install -r requirements.txt
rm -f finrlx_dev.db
alembic upgrade head
python -m seed
uvicorn app.main:app --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm install
npm run dev

# Run tests
cd backend && python -m pytest tests/ -v   # Expected: 18 passed
```

## New API Endpoints

| Endpoint | Returns |
|---|---|
| GET /api/v1/engines/comparison | 5 engines with stance, confidence, weight, drivers, ignores, risk, horizon |
| GET /api/v1/engines/disagreement | 2 agree, 3 dissent, dispersion 37%, summary text |
| GET /api/v1/engines/evidence | 5 numbered evidence items with delta labels and source engines |
| GET /api/v1/regime | Regime "Risk-on · late-cycle", 4 signal postures, 5 sector tilts |
| GET /api/v1/activity | 8 activity events (publish, breach, engine, note, defer, incident, backtest) |

## What Now Shows Real Backend Data

### Overview (/)
- **Regime strip**: regime label, confidence bar, alternatives, 4 signal postures with sigma values, 5 sector tilts — all from `/api/v1/regime`
- **Activity feed**: 8 typed events with actor names, descriptions, time-ago, detail text — from `/api/v1/activity`

### Decision (/decision)
- **Evidence narrative**: 5 numbered items (Earnings revisions, Price momentum, Options positioning, News sentiment, Regime filter) with delta labels and source engine tags — from `/api/v1/engines/evidence`
- **Engine disagreement**: 2/5 agree bar, dispersion 37%, dissenting engine pills (Narrative LLM, Risk-parity, Flow/options) — from `/api/v1/engines/disagreement`
- **Hero strip**: now shows engine agreement (2/5) and dispersion (37%) alongside positions and horizon
- **Risk gauges**: 5 constraint bars with limit markers (portfolio weight, sector concentration, drawdown, correlation, vol)

### Comparison (/comparison)
- **Engine matrix**: 5 rows (Momentum, Fundamentals, Narrative LLM, Risk-parity, Flow/options) × 7 columns (stance, confidence, weight, horizon, risk, top drivers) — from `/api/v1/engines/comparison`
- **Synthesis row**: blue-tinted bottom row showing weighted synthesis stance and confidence
- **Engine dispersion metric**: KPI card showing dispersion %
- **Methodology pane**: clicking any engine row opens right pane with drivers, ignores, and note

## What Still Shows Pending States

- Scenario controls (Decision page) — requires simulation engine
- Ops Command Center sections — structural shells with "Pending backend integration"
- TopBar scope chips — illustrative values
- Nav badge counts — static

## Troubleshooting

**Engine comparison shows null:** Re-seed with `rm -f finrlx_dev.db && alembic upgrade head && python -m seed`

**Activity feed empty:** Same — re-seed creates audit events
