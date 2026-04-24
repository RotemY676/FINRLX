# Phase 2 Runbook

**Updated:** 2026-04-24 (Phase 2.5 polish)

## Startup

No new infrastructure required beyond Phase 0+1.

### Quick start (local dev, no Docker)
```bash
# Terminal 1: Backend
cd backend
pip install -r requirements.txt
alembic upgrade head
python -m seed
uvicorn app.main:app --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

The frontend dev server defaults to port 3000. If port 3000 is occupied, Next.js will automatically use the next available port (typically 3001). Check the terminal output for the actual URL.

### Run tests
```bash
cd backend
python -m pytest tests/ -v
# Expected: 8 passed (6 from Phase 0+1, 2 from Phase 2)
```

---

## URLs to Verify

Adjust port if frontend is running on 3001 or another port.

| Page / Endpoint | URL | What to Expect |
|---|---|---|
| Overview page | http://localhost:3000 | Recommendation card with confidence bars, health panel |
| Decision Workspace | http://localhost:3000/decision | Full workspace: rationale, trust, weights chart, positions table, 4 pipeline stages |
| Comparison | http://localhost:3000/comparison | Side-by-side bar chart, comparison table, active weight metrics |
| Replay | http://localhost:3000/replay | Placeholder page |
| Backtests | http://localhost:3000/backtests | Placeholder page |
| Paper | http://localhost:3000/paper | Placeholder page |
| Admin | http://localhost:3000/admin | Placeholder page |
| Backend Health | http://localhost:8000/health | `{"status": "ok", "version": "0.1.0"}` |
| API Health (DB) | http://localhost:8000/api/v1/health | `status: ok, database: connected` |
| API Overview | http://localhost:8000/api/v1/overview | Recommendation summary with 10 positions |
| Recommendation Detail | http://localhost:8000/api/v1/recommendations/current | 10 weights with tickers |
| Decision Stages | http://localhost:8000/api/v1/recommendations/{id}/stages | selection, allocation, timing, risk_overlay |
| Comparison | http://localhost:8000/api/v1/comparison/current | 10 rows, total_active_weight |
| Swagger | http://localhost:8000/docs | All 7 endpoints listed |

---

## Manual Verification Checklist

### Overview (/)
- [ ] Page heading says "Overview"
- [ ] Recommendation card shows "published" badge, 10 positions
- [ ] Confidence bars show Model 78%, Data 92%, Operational 95%
- [ ] Warning count shows "1 warning active"
- [ ] Health panel shows 4 green dots (all OK)
- [ ] Activity shows 1 published recommendation

### Decision Workspace (/decision)
- [ ] Page heading says "Decision Workspace"
- [ ] "published" status badge in top-right
- [ ] Rationale card contains text about technology overweight
- [ ] Trust section shows 3 confidence bars
- [ ] Warnings section shows NVDA concentration cap warning
- [ ] Bar chart shows 10 bars, colored: green (overweight), red (underweight), blue (neutral)
- [ ] Stance color legend appears below chart
- [ ] Positions table shows 10 rows with ticker, name, weight, delta, stance
- [ ] Table header says "Click a row to inspect"
- [ ] Clicking any row opens right context pane with asset detail
- [ ] Context pane shows: asset name, target weight, previous weight, change, stance, rationale
- [ ] Context pane close button (×) works
- [ ] Pressing Escape closes the context pane
- [ ] Clicking a different row updates the pane content
- [ ] Decision Pipeline section shows 4 stage cards:
  - Selection: 10 included, ticker badges
  - Allocation: signal-weighted method, horizontal bars
  - Timing: "soon" urgency, 5 day horizon
  - Risk Overlay: score 42, NVDA -2% adjustment
- [ ] Metadata block shows publication dates and status

### Comparison (/comparison)
- [ ] Page heading says "Engine Comparison"
- [ ] Subtitle says "Recommendation vs Equal Weight"
- [ ] Total Active Weight metric shows ~22%
- [ ] Top 3 Concentration shows 41% (rec) vs 30% (bench)
- [ ] Confidence block shows 3 bars
- [ ] Bar chart shows paired blue/gray bars for each ticker
- [ ] Legend shows "Recommendation" and "Benchmark"
- [ ] Table shows 10 rows with rec weight, bench weight, active weight, stance
- [ ] Table header says "Click a row to inspect"
- [ ] Clicking any row opens right pane with comparison detail
- [ ] Rationale card shows recommendation rationale
- [ ] Warning indicator shows 1 active warning

### Error States
- [ ] Stop backend, reload any page → shows error with red border, message, and hint
- [ ] Backend running but no seed → shows empty state with centered message

### Context Pane Behavior
- [ ] Pane opens from right, 320px wide
- [ ] Header has sticky background and visible close button
- [ ] Footer shows "Press Esc or click × to close"
- [ ] Content scrolls independently if tall
- [ ] Pane replaces content when clicking a different row (not stacked)

---

## Troubleshooting

**Frontend starts on port 3001 instead of 3000:**
- Another process is using port 3000. This is normal; Next.js auto-selects the next port.
- Check terminal output for actual URL.

**Charts show blank area:**
- Ensure `recharts` is installed: run `npm install` in frontend/
- Recharts requires client-side rendering; chart components are marked `"use client"`

**Decision page shows "No Published Recommendation":**
- Backend must be running on port 8000 and seeded
- Verify: `curl http://localhost:8000/api/v1/recommendations/current`

**Context pane doesn't open:**
- Click directly on a table row (not on the header row)
- The pane only opens from WeightsTable and Comparison table rows

**Loading dots don't animate:**
- Tailwind `animate-pulse` requires Tailwind CSS to be loaded correctly
- If styles are missing, run `npm run dev` to rebuild
