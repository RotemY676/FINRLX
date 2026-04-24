# Design Sprint 4 Runbook

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
cd backend && python -m pytest tests/ -v   # Expected: 39 passed
```

## New API Endpoints

| Endpoint | Method | Returns |
|---|---|---|
| POST /api/v1/scenario/simulate | POST | Scenario deltas (weight, confidence, expected return) + warnings |
| GET /api/v1/scenario/baseline | GET | Default scenario parameters (horizon=42d, rate_shock=0, etc.) |
| POST /api/v1/actions/save-thesis | POST | `{ success, new_status: "staged", message }` |
| POST /api/v1/actions/promote-paper | POST | `{ success, new_status: "paper", message }` |
| POST /api/v1/actions/defer | POST | `{ success, new_status: "deferred", message }` — accepts `{ reason }` body |

## What Changed

### Decision Page (/decision)
- **Scenario controls** — was "Pending" shell, now full interactive card:
  - 4 sliders (horizon, rate shock, correlation, earnings revision weight)
  - 3 toggles (momentum engine, flow engine, policy constraints)
  - Live delta preview showing baseline → modified values
  - Warnings for extreme parameter combinations
- **Action bar** — 3 primary buttons now wired to backend:
  - "Save as current thesis" → POST /actions/save-thesis
  - "Promote to paper" → POST /actions/promote-paper
  - "Defer decision" → POST /actions/defer
  - Success/failure feedback displayed inline
- **Secondary buttons** added: Bookmark, Share, More menu (UI-only)

### Ops Command Center (/admin)
- **Incident drawer** — clicking any incident card opens a slide-over panel:
  - Header with severity badge, ID, title, metadata
  - Impact description
  - Event timeline (5 illustrative events)
  - Affected recommendations table
  - Action buttons: Open runbook, Page on-call, Snooze, Mark resolved

## Scenario Simulation Examples

```bash
# Baseline (no changes)
curl -X POST http://localhost:8000/api/v1/scenario/simulate \
  -H "Content-Type: application/json" \
  -d '{"horizon_days":42,"rate_shock_bps":0,"correlation":0.55,"earnings_revision_weight":0.6,"momentum_engine_on":true,"flow_engine_on":false,"policy_constraints_on":true}'
# → is_modified: false

# Modified scenario
curl -X POST http://localhost:8000/api/v1/scenario/simulate \
  -H "Content-Type: application/json" \
  -d '{"horizon_days":90,"rate_shock_bps":100,"correlation":0.8,"earnings_revision_weight":0.4,"momentum_engine_on":true,"flow_engine_on":true,"policy_constraints_on":false}'
# → is_modified: true, 3 deltas, warnings about rate shock and policy
```

## Troubleshooting

**Scenario controls show "Simulating..." forever:** Check that backend is running and `/api/v1/scenario/simulate` returns 200.

**Action buttons don't respond:** Check browser console for CORS/network errors. Backend must be running on port 8000.

**Incident drawer doesn't open:** Ensure you're clicking the incident card, not just the text. Check for JavaScript errors.
