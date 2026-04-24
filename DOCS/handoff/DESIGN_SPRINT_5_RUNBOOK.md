# Design Sprint 5 Runbook

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
cd backend && python -m pytest tests/ -v   # Expected: 45 passed
```

## New API Endpoints

| Endpoint | Method | Returns |
|---|---|---|
| GET /api/v1/pricechart?ticker=NVDA | GET | Time-series (16 points) + benchmark + confidence band + events |
| POST /api/v1/ops/incidents/{id}/resolve | POST | Resolves incident, creates audit event |

## What Changed

### Decision Page (/decision)
- **Price chart** — new section below evidence, showing price line + benchmark + confidence band + event markers for the top-weighted ticker

### Comparison Page (/comparison)
- **Alignment chart upgraded** — synthesis diamond marker, grid lines at 25/50/75%, SELL/HOLD/BUY labels, color legend

### Shell
- **Density selector** — "Aa" button in TopBar cycles compact/default/comfortable
- **Scope chips** — horizon now computed from recommendation dates, universe from overview

### Ops Command Center (/admin)
- **Engine drift** — now computed from consecutive signal_runs (avg confidence delta)
- **Incident resolve** — POST endpoint to mark incidents resolved

## Visual Verification Checklist

When opening the app for the first time, verify:

1. **Overview (/)** — regime strip, activity feed, KPI cards
2. **Decision (/decision)** — hero strip, evidence, disagreement, price chart, scenario sliders, action buttons
3. **Comparison (/comparison)** — engine matrix, alignment scatter with synthesis diamond, weight bars
4. **Ops (/admin)** — KPI strip, queue with filter/actions, feeds, engines, breaches, incidents (click for drawer), audit with scope filter
5. **Dark theme** — click moon icon in TopBar, verify all sections
6. **Density** — click "Aa" button, verify compact/comfortable spacing
7. **Scope chips** — should show live regime label, 5d horizon, US Large Cap

## Troubleshooting

**Price chart shows "Loading...":** Check `/api/v1/pricechart?ticker=NVDA` returns 200.

**Alignment chart missing synthesis point:** Check that engine comparison data includes `synthesis_stance` and `synthesis_confidence`.

**Density button missing:** Only visible on large screens (hidden below lg breakpoint).
