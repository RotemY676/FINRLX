# Design Sprint 3 Runbook

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
cd backend && python -m pytest tests/ -v   # Expected: 30 passed
```

## New API Endpoints

| Endpoint | Method | Returns |
|---|---|---|
| GET /api/v1/ops | GET | Full ops dashboard: queue, feeds, engines, breaches, incidents, audit, system_kpis |
| GET /api/v1/ops/queue | GET | Pending queue items. Filter: `?filter=all\|high` |
| GET /api/v1/ops/feeds | GET | Data feed statuses |
| GET /api/v1/ops/engines | GET | Engine health computed from signal_runs |
| GET /api/v1/ops/breaches | GET | Active policy breaches |
| GET /api/v1/ops/incidents | GET | Open (non-resolved) incidents |
| GET /api/v1/ops/audit | GET | Audit trail. Filter: `?scope=all\|recommendation\|breach\|engine\|...` |
| POST /api/v1/ops/queue/{id}/approve | POST | Approve queue item, creates audit event |
| POST /api/v1/ops/queue/{id}/defer | POST | Defer queue item, creates audit event |
| POST /api/v1/ops/queue/{id}/challenge | POST | Challenge queue item, creates audit event |
| GET /api/v1/workspace-counts | GET | `{ overview, decisions, risk, ops }` badge counts |

## What Changed

### Ops Command Center (/admin)
- **KPI strip** at top: 6 metric cards (queue depth, feed coverage, engine health, breaches, incidents, high priority)
- **Publication Queue**: filter tabs (All / High priority), per-row action buttons (Approve / Defer / Challenge)
- **Data Feeds**: now from DB (6 feeds seeded)
- **Engine Health**: computed live from signal_runs table
- **Breach Watch**: now from DB (3 breaches seeded)
- **Incidents**: now from DB (2 incidents seeded)
- **Audit Trail**: scope filter tabs (All / Queue / Policy / Engine / Ops)

### Shell
- **Dark theme toggle**: moon icon in TopBar → switches to dark, sun icon → switches back. Persisted in localStorage
- **Dynamic scope chips**: regime label from `/regime` API, confidence-colored indicator dot
- **Dynamic sidebar badges**: live counts from `/workspace-counts`, refreshed every 60s

## What Still Shows Pending States

- Scenario controls (Decision page) — requires simulation engine
- Alignment scatter chart (Comparison) — requires bubble chart component
- Incident drawer — structured data exists, slide-over panel not yet built

## Troubleshooting

**Ops shows empty sections:** Re-seed with `rm -f finrlx_dev.db && alembic upgrade head && python -m seed`

**Dark theme flashes on load:** The blocking `<script>` in layout.tsx should prevent this. If it persists, check that `suppressHydrationWarning` is on the `<html>` tag.

**Sidebar badges show nothing:** Check that `/api/v1/workspace-counts` returns 200. Re-seed if empty.

**Queue action buttons don't work:** Check browser console for CORS or 404 errors. Ensure backend is running.
