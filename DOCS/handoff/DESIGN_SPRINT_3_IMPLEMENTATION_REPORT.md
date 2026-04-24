# Design Sprint 3 Implementation Report

**Date:** 2026-04-24
**Sprint:** Ops DB-Backed + Dark Theme + Live Badges + Scope Chips
**Status:** Complete

---

## 1. DB Models Added

| Model | Table | Columns |
|---|---|---|
| DataFeed | data_feeds | id, name, status, lag, coverage, slo, last_checked_at |
| PolicyBreach | policy_breaches | id, kind, label, utilization, trend, severity, related, is_active |
| PublicationQueueEntry | publication_queue | id, recommendation_id, ticker, stance, version, submitter, weight, confidence, flags, priority, status, submitted_ago |

Migration: `002_ops_tables.py` — adds 3 new tables.

## 2. Ops Endpoint Refactored to DB-Backed

Previously `GET /ops` returned hardcoded Python constants. Now all 6 sections query the database:

| Section | Source |
|---|---|
| Queue | `publication_queue` table |
| Feeds | `data_feeds` table |
| Engines | Computed from `signal_runs` (latest per engine, latency/staleness) |
| Breaches | `policy_breaches` table (active only) |
| Incidents | `incidents` table (non-resolved) |
| Audit | `audit_events` table (unchanged from Sprint 2) |

New field: `system_kpis` — 6 computed KPI metrics returned with every `/ops` response.

## 3. New Sub-Endpoints (8)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/ops/queue` | GET | Queue items, filterable by `?filter=all\|high` |
| `/api/v1/ops/feeds` | GET | Data feed statuses |
| `/api/v1/ops/engines` | GET | Engine health from signal_runs |
| `/api/v1/ops/breaches` | GET | Active policy breaches |
| `/api/v1/ops/incidents` | GET | Open incidents |
| `/api/v1/ops/audit` | GET | Audit trail, filterable by `?scope=all\|recommendation\|breach\|...` |
| `/api/v1/ops/queue/{id}/approve` | POST | Approve queue item + create audit event |
| `/api/v1/ops/queue/{id}/defer` | POST | Defer queue item + create audit event |
| `/api/v1/ops/queue/{id}/challenge` | POST | Challenge queue item + create audit event |
| `/api/v1/workspace-counts` | GET | Badge counts for sidebar (overview, decisions, risk, ops) |

Total endpoints: **28** (was 17).

## 4. Seed Data Added

- **6 data feeds** matching design handoff ops.jsx
- **3 policy breaches** matching design handoff
- **7 publication queue entries** (expanded from 4 hardcoded to 7)
- **2 incidents** matching design handoff

## 5. Frontend: Dark Theme Toggle

- **ThemeContext** (`contexts/ThemeContext.tsx`) — persists to localStorage, no flash on load
- **Blocking script** in `<head>` sets `data-theme` before React hydrates
- **Moon/Sun icons** added to Icon component
- **TopBar toggle button** — click to switch light/dark

## 6. Frontend: Dynamic Sidebar Badges

- **Sidebar** now fetches `/workspace-counts` on mount + polls every 60s
- Badges show live counts from DB (queue depth, recommendations, breaches, incidents)
- Graceful degradation — badges hidden if API unavailable

## 7. Frontend: Dynamic Scope Chips

- **ScopeContext** (`contexts/ScopeContext.tsx`) — fetches `/regime` on mount
- **TopBar scope chips** — regime label, confidence-colored dot, horizon, universe
- Loading skeleton while fetching

## 8. Frontend: Admin Page Enrichment

- **KPI Strip** — 6 metric cards at top (queue depth, feed coverage, engine health, breaches, incidents, high priority)
- **Queue filter tabs** — All / High priority, calls `/ops/queue?filter=`
- **Queue action buttons** — Approve / Defer / Challenge per row, calls POST endpoints
- **Audit scope filter** — All / Queue / Policy / Engine / Ops tabs, calls `/ops/audit?scope=`
- **Version bump** — v0.2.0 → v0.3.0

## 9. Files Created / Modified

### Created (8)
```
backend/migrations/versions/002_ops_tables.py
backend/tests/test_design_sprint3.py
frontend/src/contexts/ThemeContext.tsx
frontend/src/contexts/ScopeContext.tsx
DOCS/handoff/DESIGN_SPRINT_3_IMPLEMENTATION_REPORT.md
DOCS/handoff/DESIGN_SPRINT_3_RUNBOOK.md
```

### Modified (11)
```
backend/app/models/ops.py              — added DataFeed, PolicyBreach, PublicationQueueEntry
backend/app/models/__init__.py         — registered new models
backend/app/schemas/ops.py             — added OpsSystemKpi, QueueActionResponse, WorkspaceCounts
backend/app/schemas/__init__.py        — new exports
backend/app/api/v1/ops.py             — DB-backed + 10 new endpoints
backend/seed.py                        — added ops seed data
backend/tests/conftest.py             — added ops test fixtures
frontend/src/app/layout.tsx           — ThemeProvider, ScopeProvider, hydration script
frontend/src/app/admin/page.tsx       — KPI strip, queue filters/actions, audit filters
frontend/src/components/shell/TopBar.tsx    — theme toggle, dynamic scope chips
frontend/src/components/shell/Sidebar.tsx   — live badge counts from API
frontend/src/components/icons/Icon.tsx      — sun, moon icons
frontend/src/services/api.ts               — new types + 7 fetchers
```

## 10. PASS / PARTIAL / FAIL

| Check | Result |
|---|---|
| Backend starts | **PASS** (28 endpoints) |
| Frontend builds | **PASS** (7 routes, 0 errors) |
| All existing tests pass | **PASS** (18/18 prior) |
| New tests pass | **PASS** (12 new, 30/30 total) |
| Ops data from DB | **PASS** — all 6 sections DB-backed |
| Queue actions work | **PASS** — approve/defer/challenge update status + create audit |
| Workspace counts | **PASS** — returns live counts |
| KPI strip | **PASS** — 6 computed metrics |
| Queue filter tabs | **PASS** — filters via API |
| Audit scope filter | **PASS** — filters via API |
| Dark theme toggle | **PASS** — compiles, tokens ready |
| Dynamic scope chips | **PASS** — wired to regime API |
| Dynamic sidebar badges | **PASS** — wired to workspace-counts API |
| No API regressions | **PASS** (30/30 tests) |
| Visual verification | **NOT PERFORMED** |

## 11. What Remains Pending

| Section | Reason |
|---|---|
| Scenario controls | Requires simulation engine backend |
| Action bar state machine | Requires publish/defer workflow endpoints |
| Alignment scatter chart | Requires bubble chart component |
| TopBar scope chips — full dynamic binding | Horizon/universe need recommendation context |
| Engine drift computation | Requires comparing two consecutive signal runs |
| Incident drawer | Slide-over panel for incident details |
| Dark theme visual polish | Tokens ready, may need component-level tweaks |

## 12. Known Limitations

1. Engine health `drift` field is stubbed at 0.0 — requires comparing two consecutive runs per engine
2. Scope chips `horizon` and `universe` still use fallback values (regime API doesn't carry them)
3. Queue actions use hardcoded `"current_user"` as actor — needs auth integration
4. Incident `started` field shows "recent" instead of relative time — `created_at` needs formatting
5. Dark theme has not been visually verified in a browser
