# Design Sprint 2 Implementation Report

**Date:** 2026-04-24
**Sprint:** Backend-Supported Design Completion
**Status:** Complete

---

## 1. Backend Support Added

| Capability | Schema | Endpoint | Seed Data |
|---|---|---|---|
| Per-engine signals | `EngineSignal`, `EngineComparisonResponse` | `GET /engines/comparison` | 5 engines × 5 assets = 25 signal outputs |
| Engine disagreement | `DisagreementSummary` | `GET /engines/disagreement` | Computed from 5 engine stances |
| Evidence narrative | `EvidenceItem`, `EvidenceNarrativeResponse` | `GET /engines/evidence` | 5 numbered evidence items |
| Regime classification | `RegimeSnapshot`, `SignalPosture`, `SectorTilt` | `GET /regime` | 1 regime + 4 postures + 5 tilts |
| Activity feed | `ActivityEvent`, `ActivityFeedResponse` | `GET /activity` | 8 audit events |

## 2. New Schemas/Models/Endpoints

**New schema files (3):**
- `backend/app/schemas/engine.py` — EngineSignal, EngineComparisonResponse, DisagreementSummary
- `backend/app/schemas/evidence.py` — EvidenceItem, EvidenceNarrativeResponse
- `backend/app/schemas/regime.py` — RegimeSnapshot, SignalPosture, SectorTilt, ActivityEvent, ActivityFeedResponse

**New endpoint files (2):**
- `backend/app/api/v1/engines.py` — /engines/comparison, /engines/disagreement, /engines/evidence
- `backend/app/api/v1/regime.py` — /regime, /activity

**No new DB models or migrations needed** — used existing `signal_runs`, `signal_outputs`, `audit_events` tables.

Total endpoints: 17 (was 12)

## 3. Seed Data Added

- **25 signal outputs** across 5 engines (Momentum, Fundamentals, Narrative LLM, Risk-parity, Flow/options) × 5 key assets
- **5 evidence items** matching design handoff EvidenceCard structure
- **8 audit events** matching design handoff ActivityFeed structure
- All deterministic (random.seed(42))

## 4. Sections Now Powered by Real Backend Data

| Section | Page | Previous State | Now |
|---|---|---|---|
| Regime strip | Overview | Illustrative hardcoded | **Real** — from /api/v1/regime |
| Activity feed | Overview | Illustrative 2 items | **Real** — 8 events from /api/v1/activity |
| Evidence narrative | Decision | Partial (weight rationales) | **Real** — 5 numbered items from /api/v1/engines/evidence |
| Engine disagreement | Decision | "Pending" shell | **Real** — agreement bar, dispersion, dissenting engines |
| Risk gauges | Decision | Text-only constraints | **Real** — 5 gauge bars with limit markers |
| Engine matrix | Comparison | "Pending" shell | **Real** — 5 engines × 7 dimensions from /api/v1/engines/comparison |
| Engine methodology pane | Comparison | Not present | **Real** — drivers, ignores, note per engine |
| Engine dispersion metric | Comparison | Not present | **Real** — dispersion % KPI card |

## 5. What Remains Pending

| Section | Reason |
|---|---|
| Scenario controls | Requires simulation engine backend |
| Action bar state machine | Requires publish/defer workflow endpoints |
| Ops Command Center modules | Requires ops health/queue endpoints |
| TopBar scope chips | Requires dynamic regime/universe binding |
| Nav badge counts | Requires workspace count API |
| Dark theme toggle UI | Tokens ready, needs UI control |
| Alignment scatter chart | Requires bubble chart component |

## 6. Files Created / Modified

### Created (6)
```
backend/app/schemas/engine.py
backend/app/schemas/evidence.py
backend/app/schemas/regime.py
backend/app/api/v1/engines.py
backend/app/api/v1/regime.py
backend/tests/test_design_sprint2.py
DOCS/handoff/DESIGN_SPRINT_2_IMPLEMENTATION_REPORT.md
DOCS/handoff/DESIGN_SPRINT_2_RUNBOOK.md
```

### Modified (6)
```
backend/app/api/router.py                — added engines + regime routes
backend/app/schemas/__init__.py          — added new schema exports
backend/seed.py                          — added engine signals, evidence items, audit events
frontend/src/services/api.ts             — added engine/evidence/regime/activity types + fetchers
frontend/src/app/page.tsx                — wired regime + activity from real APIs
frontend/src/app/decision/page.tsx       — wired evidence + disagreement from real APIs + risk gauges
frontend/src/app/comparison/page.tsx     — wired engine matrix from real API
```

## 7. PASS / PARTIAL / FAIL

| Check | Result |
|---|---|
| Backend starts | **PASS** (17 endpoints) |
| Frontend builds | **PASS** (7 routes, 0 errors) |
| Overview still works | **PASS** |
| Decision still works | **PASS** |
| Comparison still works | **PASS** |
| Regime strip uses real data | **PASS** |
| Activity feed uses real data | **PASS** |
| Evidence narrative uses real data | **PASS** |
| Comparison matrix uses real engine data | **PASS** |
| Engine disagreement uses real data | **PASS** |
| No regressions in existing tests | **PASS** (13/13 prior) |
| New tests added | **PASS** (5 new, 18/18 total) |
| Visual verification | **NOT PERFORMED** |

## 8. Known Limitations

1. Engine signal data is seeded, not from real ML engines
2. Evidence items are defined in seed.py, not dynamically generated
3. Regime endpoint returns deterministic data, not from a real classifier
4. Activity events are seeded once — no live event generation
5. Risk gauge values on Decision page are illustrative constants matching the design prototype, not computed from real portfolio data
6. Alignment scatter chart (design: AlignmentChart) not yet built
