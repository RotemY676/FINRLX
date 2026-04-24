# Design Sprint 4 Implementation Report

**Date:** 2026-04-24
**Sprint:** Scenario Engine + Action Bar + Incident Drawer
**Status:** Complete

---

## 1. Scenario Simulation Engine

### Backend
- **Schema:** `ScenarioParams` (7 fields: horizon, rate shock, correlation, earnings weight, 3 toggles), `ScenarioResult` (deltas, impacts, warnings)
- **Endpoint:** `POST /scenario/simulate` — simplified linear simulation model
- **Endpoint:** `GET /scenario/baseline` — returns default parameter values
- **Simulation logic:** Computes delta impacts based on parameter deviation from baseline. Sensitivity coefficients for horizon, rate shock, correlation, earnings weight, and engine toggles. Produces 3 delta previews (Weight, Confidence, Expected Return) and contextual warnings.

### Frontend — ScenarioCard Component
- **4 interactive sliders:** Horizon (7–180d), Rate shock (±200bps), Correlation (0.00–1.00), Earnings revision weight (0–100%)
- **3 toggle switches:** Momentum engine, Flow/options engine, Policy constraints
- **Baseline/Modified indicator** with Reset button
- **Delta preview strip** — shows baseline → modified for Weight, Confidence, Expected Return
- **Warning display** for extreme parameter combinations
- **Apply to thesis / Discard buttons** when modified
- **Loading spinner** during API call
- Calls `POST /scenario/simulate` on every parameter change (debounced by React state)

## 2. Action Bar State Machine

### Backend
- **Endpoint:** `POST /actions/save-thesis` — sets status to "staged", creates audit event
- **Endpoint:** `POST /actions/promote-paper` — sets status to "paper", creates audit event
- **Endpoint:** `POST /actions/defer` — sets status to "deferred", accepts optional reason, creates audit event

### Frontend
- **3 primary action buttons** wired to backend with loading state and success feedback
- **3 secondary buttons** added: Bookmark, Share, More menu (matching design handoff ActionBar)
- **Success message** displays inline with animation after action completes
- Buttons disabled while action is in-flight

## 3. Incident Drawer

### Component: IncidentDrawer
- **Slide-over modal** — opens from right side with backdrop overlay
- **Header:** Severity badge, incident ID, title, metadata (started, owner, status), close button
- **Impact section:** Description text + affected recommendation count
- **Timeline:** 5 illustrative events with colored dots and time labels
- **Affected recommendations table:** Rec ID, engine impact, capped confidence, status pill
- **Action buttons:** Open runbook, Page on-call, Snooze 15m, Mark resolved
- **Integrated into admin page** — clicking any incident card opens the drawer

## 4. New Endpoints Summary

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/scenario/simulate` | POST | Run scenario simulation with modified params |
| `/api/v1/scenario/baseline` | GET | Get baseline parameter values |
| `/api/v1/actions/save-thesis` | POST | Save recommendation as current thesis |
| `/api/v1/actions/promote-paper` | POST | Promote to paper portfolio |
| `/api/v1/actions/defer` | POST | Defer decision with optional reason |

Total endpoints: **33** (was 28).

## 5. Files Created / Modified

### Created (8)
```
backend/app/schemas/scenario.py
backend/app/schemas/action.py
backend/app/api/v1/scenario.py
backend/app/api/v1/actions.py
backend/tests/test_design_sprint4.py
frontend/src/components/decision/ScenarioCard.tsx
frontend/src/components/ops/IncidentDrawer.tsx
DOCS/handoff/DESIGN_SPRINT_4_IMPLEMENTATION_REPORT.md
DOCS/handoff/DESIGN_SPRINT_4_RUNBOOK.md
```

### Modified (5)
```
backend/app/api/router.py              — added scenario + actions routers
backend/app/schemas/__init__.py        — new exports
frontend/src/app/decision/page.tsx     — wired action bar + replaced scenario shell with ScenarioCard
frontend/src/app/admin/page.tsx        — added IncidentDrawer integration
frontend/src/services/api.ts           — added scenario + action types and fetchers
```

## 6. PASS / PARTIAL / FAIL

| Check | Result |
|---|---|
| Backend starts | **PASS** (33 endpoints) |
| Frontend builds | **PASS** (7 routes, 0 errors) |
| All existing tests pass | **PASS** (30/30 prior) |
| New tests pass | **PASS** (9 new, 39/39 total) |
| Scenario baseline returns defaults | **PASS** |
| Scenario modified returns deltas | **PASS** |
| Scenario validation rejects invalid params | **PASS** |
| Scenario warnings for extreme params | **PASS** |
| Action save-thesis works | **PASS** |
| Action promote-paper works | **PASS** |
| Action defer works | **PASS** |
| No regressions | **PASS** (39/39 tests) |
| Visual verification | **NOT PERFORMED** |

## 7. What Remains Pending

| Section | Reason |
|---|---|
| Alignment scatter chart | Requires bubble chart component (Recharts or custom SVG) |
| Engine drift computation | Requires comparing two consecutive signal_runs |
| Horizon/Universe scope chips | Need recommendation context for dynamic values |
| Incident drawer — real timeline data | Currently uses illustrative data |
| Incident drawer — Mark resolved action | Needs backend endpoint to resolve incidents |
| Dark theme visual polish | Tokens ready, needs QA pass |
| Density selector UI | System ready, needs toggle control |
| Chart card with event markers | Design shows time-series with bands |
| Mobile/responsive adaptation | Shell should collapse context to bottom sheet |

## 8. Known Limitations

1. Scenario simulation is a simplified linear model — a real implementation would re-run the full engine pipeline
2. "Apply to thesis" button in ScenarioCard is UI-only — does not yet persist scenario overrides
3. Action bar uses hardcoded "current_user" as actor — needs auth integration
4. Incident drawer timeline and affected recs are illustrative (hardcoded in component)
5. Bookmark, Share, More menu buttons are UI-only (no backend)
6. Action tests restore recommendation status after each test to avoid polluting shared test DB state
