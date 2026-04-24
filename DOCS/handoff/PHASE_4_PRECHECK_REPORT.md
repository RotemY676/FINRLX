# Phase 4 Precheck Report

**Date:** 2026-04-24
**Purpose:** Verify current implementation against the main DOCS-driven plan before coding Phase 4 Backend Pipeline Core.
**Method:** Direct code inspection. No claims from prior reports trusted without file-level evidence.

---

## 1. Current Repo Truth Table

### 1.1 Existing DB Tables (21 tables across 2 migrations)

**Migration 001_initial (18 tables):**

| Table | Domain (Doc 11) | Model Class | Has Real Logic |
|---|---|---|---|
| `assets` | 1 - Reference | Asset | Seed-only |
| `universes` | 1 - Reference | Universe | Seed-only |
| `universe_memberships` | 1 - Reference | UniverseMembership | Seed-only |
| `benchmarks` | 1 - Reference | Benchmark | Seed-only (empty) |
| `recommendations` | 6 - Recommendation | Recommendation | Seed-only |
| `recommendation_weights` | 6 - Recommendation | RecommendationWeight | Seed-only |
| `selection_runs` | 5 - Decision Pipeline | SelectionRun | Seed-only |
| `allocation_results` | 5 - Decision Pipeline | AllocationResult | Seed-only |
| `timing_results` | 5 - Decision Pipeline | TimingResult | Seed-only |
| `risk_overlay_results` | 5 - Decision Pipeline | RiskOverlayResult | Seed-only |
| `signal_runs` | 4 - Signals | SignalRun | Seed-only |
| `signal_outputs` | 4 - Signals | SignalOutput | Seed-only |
| `backtest_experiments` | 7 - Validation | BacktestExperiment | Seed-only |
| `paper_portfolios` | 7 - Validation | PaperPortfolio | Seed-only |
| `replay_snapshots` | 7 - Validation | ReplaySnapshot | Seed-only |
| `audit_events` | 8 - Admin/Ops | AuditEvent | DB-backed (actions write) |
| `incidents` | 8 - Admin/Ops | Incident | Seed + resolve endpoint |
| `system_health_snapshots` | 8 - Admin/Ops | SystemHealthSnapshot | Empty (unused) |

**Migration 002_ops_tables (3 tables):**

| Table | Domain | Model Class | Has Real Logic |
|---|---|---|---|
| `data_feeds` | 8 - Admin/Ops | DataFeed | Seed-only |
| `policy_breaches` | 8 - Admin/Ops | PolicyBreach | Seed-only |
| `publication_queue` | 8 - Admin/Ops | PublicationQueueEntry | Seed + queue actions |

### 1.2 Existing Models (22 model classes in 7 files)

| File | Classes |
|---|---|
| `models/base.py` | TimestampMixin (mixin only) |
| `models/reference.py` | Asset, Universe, UniverseMembership, Benchmark |
| `models/recommendation.py` | PublicationStatus (enum), Recommendation, RecommendationWeight |
| `models/decision_pipeline.py` | SelectionRun, AllocationResult, TimingResult, RiskOverlayResult |
| `models/signal.py` | SignalRun, SignalOutput |
| `models/validation.py` | BacktestExperiment, PaperPortfolio, ReplaySnapshot |
| `models/ops.py` | AuditEvent, Incident, SystemHealthSnapshot, DataFeed, PolicyBreach, PublicationQueueEntry |

### 1.3 Existing Schemas (14 schema files)

| File | Key Types |
|---|---|
| `schemas/common.py` | ApiResponse[T], ResponseMeta, FreshnessState, TypedError, ErrorResponse |
| `schemas/recommendation.py` | ConfidenceTriplet, WeightEntry, RecommendationSummary, RecommendationDetail |
| `schemas/decision.py` | SelectionRunView, AllocationView, TimingView, RiskOverlayView, DecisionStagesResponse |
| `schemas/comparison.py` | ComparisonResponse, ComparisonWeightRow |
| `schemas/overview.py` | OverviewResponse, HealthSummary |
| `schemas/replay.py` | ReplayDetail, ReplayListResponse |
| `schemas/backtest.py` | BacktestDetail, BacktestListResponse |
| `schemas/paper.py` | PaperPortfolioDetail |
| `schemas/engine.py` | EngineSignal, EngineComparisonResponse, DisagreementSummary |
| `schemas/evidence.py` | EvidenceItem, EvidenceNarrativeResponse |
| `schemas/regime.py` | RegimeSnapshot, ActivityFeedResponse, ActivityEvent |
| `schemas/ops.py` | OpsCommandCenterResponse, OpsSystemKpi, QueueActionResponse, WorkspaceCounts, + 6 item types |
| `schemas/scenario.py` | ScenarioParams, ScenarioResult, ScenarioDelta |
| `schemas/action.py` | ActionResult, DeferRequest |
| `schemas/pricechart.py` | PriceChartData, PricePoint, ChartEvent |

### 1.4 Existing API Endpoints (36 endpoints in 14 files)

| File | Endpoints | Data Source |
|---|---|---|
| `actions.py` | POST save-thesis, promote-paper, defer | DB-BACKED |
| `backtests.py` | GET /backtests, GET /backtests/{id} | DB-BACKED (seed data) |
| `comparison.py` | GET /comparison/current | DB-BACKED (seed data) |
| `decision.py` | GET /recommendations/{id}/stages | DB-BACKED (seed data) |
| `engines.py` | GET engines/comparison, disagreement, evidence | DB-BACKED (seed data) |
| `health.py` | GET /health | DB-BACKED (static) |
| `ops.py` | GET ops + 6 sub-endpoints + 3 queue actions + resolve + workspace-counts | DB-BACKED |
| `overview.py` | GET /overview | DB-BACKED (seed data) |
| `paper.py` | GET /paper/current | DB-BACKED (seed data) |
| `pricechart.py` | GET /pricechart | **HARDCODED** (no DB, seeded RNG) |
| `recommendations.py` | GET /recommendations/current, GET /{id} | DB-BACKED (seed data) |
| `regime.py` | GET /regime | **HARDCODED** (zero DB interaction, returns static literals) |
| `regime.py` | GET /activity | DB-BACKED (queries audit_events) |
| `replay.py` | GET /replay, GET /replay/{id} | DB-BACKED (seed data) |
| `scenario.py` | POST /scenario/simulate, GET /scenario/baseline | **HARDCODED** (no DB, linear model) |

### 1.5 Existing Frontend Pages (7 pages, 28 components)

| Route | Page | API Calls | Status |
|---|---|---|---|
| `/` | Overview | fetchOverview, fetchRegime, fetchActivity | Wired to API |
| `/decision` | Decision Workspace | fetchCurrentRecommendation, fetchDecisionStages, fetchEvidence, fetchDisagreement, simulateScenario, action* | Wired to API |
| `/comparison` | Engine Comparison | fetchCurrentComparison, fetchEngineComparison | Wired to API |
| `/replay` | Replay & Forensics | fetchReplayList, fetchReplay | Wired to API |
| `/backtests` | Backtests | fetchBacktestList, fetchBacktest | Wired to API |
| `/paper` | Paper Portfolio | fetchCurrentPaper | Wired to API |
| `/admin` | Ops Command Center | fetchOps, fetchOpsQueue, fetchOpsAudit, queue actions | Wired to API |

**Shell components:** AppShell, TopBar (theme toggle, density selector, dynamic scope chips), Sidebar (live badge counts), ContextPane (tabbed panels)

**Contexts:** ThemeContext (dark/light), ScopeContext (regime/horizon/universe from API)

### 1.6 Existing Tests (45 tests in 7 files)

| File | Tests | Coverage |
|---|---|---|
| `test_smoke.py` | 6 | Root health, API health, overview, recommendation, envelope |
| `test_phase2.py` | 2 | Decision stages, comparison |
| `test_phase3.py` | 3 | Replay list, replay detail, backtests, paper |
| `test_design_sprint2.py` | 5 | Engine comparison, disagreement, evidence, regime, activity |
| `test_design_sprint3.py` | 12 | Full ops, sub-endpoints, queue filter, queue action, workspace counts |
| `test_design_sprint4.py` | 9 | Scenario baseline/simulate/validate/warnings, action save/promote/defer |
| `test_design_sprint5.py` | 6 | Price chart (3 tickers), engine drift, incident resolve, scenario regression |

---

## 2. Main-Plan Alignment

### 2.1 Phase 0–3 Completion Status

| Phase | Claim | Verified Status | Evidence |
|---|---|---|---|
| **Phase 0 — Foundation** | FastAPI + SQLAlchemy + Alembic + CORS | **PASS** | `main.py`, `database.py`, `config.py`, `alembic.ini` all present and functional |
| **Phase 1 — Data Contracts** | 18 tables, Pydantic schemas, seed script | **PASS** | 21 tables in migrations, 22 model classes, 14 schema files, seed.py populates all |
| **Phase 2 — Decision Workspace** | Decision stages, comparison endpoints | **PARTIAL** | Endpoints exist and return seed data. No real pipeline computation exists. |
| **Phase 3 — Validation Surfaces** | Replay, backtests, paper endpoints | **PARTIAL** | Endpoints exist. Data is static seed. No real backtest engine, no real paper tracking, no real replay reconstruction. |

### 2.2 What is Truly Complete vs Seeded/Demo

**Truly complete (real functional logic):**
- FastAPI application bootstrap, routing, middleware, CORS
- Async database layer with SQLAlchemy + Alembic migrations
- API envelope/metadata system (ApiResponse, ResponseMeta, trace_id, freshness)
- Ops queue actions (approve/defer/challenge) — actually mutate DB + create audit events
- Action bar (save-thesis/promote-paper/defer) — actually mutate recommendation status
- Incident resolve — actually mutates incident status
- Workspace counts — real DB aggregate queries
- Engine drift computation — real comparison of signal_run confidences
- Theme/density/scope UI controls — real client state management

**Seed-only (queries DB but DB only has seed data — no real pipeline produces it):**
- All recommendation data (1 seeded recommendation)
- All weight data (10 seeded weights)
- All decision pipeline stages (1 seeded each)
- All signal runs/outputs (5 engines × 5 assets = 25 seeded outputs)
- All evidence items (5 seeded, defined in seed.py constants)
- Activity feed (8 seeded audit events)
- Regime endpoint (returns seed data from engine outputs)
- Backtest experiment (1 seeded with random equity curve)
- Paper portfolio (1 seeded with random drift)
- Replay snapshots (5 seeded stage snapshots)
- Data feeds (6 seeded)
- Policy breaches (3 seeded)
- Publication queue (7 seeded)
- Incidents (2 seeded)

**Hardcoded constants leaking into "DB-backed" endpoints:**
- `/engines/comparison` queries DB for signal_runs but maps results through `ENGINE_DEFS` constant from `seed.py` for all display properties (stance, confidence, drivers, ignores, note). A new engine added to DB would be ignored.
- `/engines/disagreement` dispersion value (0.37) is computed from `ENGINE_DEFS`, not DB.
- `/engines/evidence` returns `EVIDENCE_ITEMS` constant from `seed.py` — zero DB content.
- `/regime` is fully hardcoded — zero DB interaction, returns static literals on every call.
- `HealthSummary` in `/overview` returns all-true defaults — never queries `system_health_snapshots` or `incidents` tables.

**Fully hardcoded (no DB at all):**
- `pricechart.py` — generates fake price series with `random.seed(42)`
- `scenario.py` — linear sensitivity model with hardcoded baseline constants

**Defined but unused models/schemas:**
- `Benchmark` model — never queried by any endpoint (comparison uses equal-weight computed on the fly)
- `SystemHealthSnapshot` model — never queried by any endpoint
- `PaginationCursor` schema — defined in common.py but never used

### 2.3 What Phase 4 Already Exists Partially

| Component | Status | What Exists | What's Missing |
|---|---|---|---|
| Signal run/output schema | **Tables exist** | `signal_runs`, `signal_outputs` with correct columns | No code to actually run engines and produce outputs |
| Decision pipeline schema | **Tables exist** | `selection_runs`, `allocation_results`, `timing_results`, `risk_overlay_results` | No code to actually compute pipeline stages |
| Recommendation schema | **Table exists** | `recommendations`, `recommendation_weights` | No code to assemble recommendation from pipeline output |
| Publication workflow | **Partial** | Queue actions exist. Status field on Recommendation. | No publication gate logic, no policy evaluation, no approval flow |
| Ingestion layer | **MISSING** | No tables, no models, no endpoints | Need market_bars, news_events, raw manifests |
| Feature registry | **MISSING** | No tables, no models | Need feature_sets, feature_recipes per Doc 11 Domain 3 |
| Engine runner | **MISSING** | No orchestration code | Need scheduled/triggered engine execution |
| Policy engine | **MISSING** | No guardrail evaluation code | Need rule engine per Doc 14 |

### 2.4 What Phase 4 is Missing (per Doc 10 Section 8 Canonical Production Flow)

The canonical flow from Doc 10 is:
1. ⛔ Acquire/refresh raw inputs → **No ingestion code exists**
2. ⛔ Normalize timestamps, store curated inputs → **No normalization code exists**
3. ⛔ Compute/refresh feature sets → **No feature computation exists**
4. ⛔ Run engine-level signals → **No engine runner exists**
5. ⛔ Execute selection policy → **No selection computation exists**
6. ⛔ Execute allocation policy → **No allocation computation exists**
7. ⛔ Execute timing policy → **No timing computation exists**
8. ⛔ Execute risk overlay → **No risk overlay computation exists**
9. ⛔ Publication gate → **No gate logic exists**
10. ✅ Emit audit events → AuditEvent model and creation exists

---

## 3. Seeded / Hardcoded / Illustrative Inventory

### 3.1 Backend Endpoints with Non-Real Data

| Endpoint | Data Source | Issue |
|---|---|---|
| GET /overview | Queries DB | Only returns the 1 seeded recommendation |
| GET /recommendations/current | Queries DB | Only returns the 1 seeded recommendation |
| GET /recommendations/{id}/stages | Queries DB | Only returns 4 seeded stages |
| GET /comparison/current | Queries DB | Only returns seeded weights vs equal-weight benchmark |
| GET /engines/comparison | Queries DB | Returns 5×5 seeded signal outputs |
| GET /engines/disagreement | Queries DB | Computes from seeded signal outputs |
| GET /engines/evidence | Queries DB | Returns evidence items defined as constants in seed.py |
| GET /regime | Queries DB | Derives regime from seeded signal_runs |
| GET /activity | Queries DB | Returns 8 seeded audit events |
| GET /replay | Queries DB | Returns list from 5 seeded snapshots |
| GET /replay/{id} | Queries DB | Returns seeded replay data |
| GET /backtests | Queries DB | Returns 1 seeded backtest with random equity curve |
| GET /paper/current | Queries DB | Returns 1 seeded paper portfolio |
| GET /pricechart | **No DB** | Hardcoded price series with `random.seed(42)` |
| POST /scenario/simulate | **No DB** | Linear sensitivity model with hardcoded coefficients |
| GET /ops/feeds | Queries DB | Returns 6 seeded feeds |
| GET /ops/breaches | Queries DB | Returns 3 seeded breaches |
| GET /ops/incidents | Queries DB | Returns 2 seeded incidents |

### 3.2 Frontend Sections with Illustrative Data

| Section | Page | Issue |
|---|---|---|
| Risk gauge bars | /decision | 5 hardcoded gauge values in page.tsx (lines 174-180) |
| Scenario simulation | /decision | Calls hardcoded backend linear model |
| Price chart | /decision | Calls hardcoded backend price generator |
| KPI "Freshness 94%" and "Coverage 96%" | / (Overview) | Hardcoded inline, not from API |
| ContextPane Risk tab | Shell | Hardcoded portfolio impact numbers and policy flags |
| ContextPane Provenance/Compare/Notes | Shell | "Awaiting backend integration" placeholder |
| Incident drawer timeline | /admin | Hardcoded 5 timeline events in IncidentDrawer.tsx |
| Incident drawer affected recs | /admin | Hardcoded 3 affected recs in IncidentDrawer.tsx |
| Incident drawer action buttons | /admin | Open runbook, Page on-call, Snooze are non-functional |
| Sidebar saved views | Shell | 4 hardcoded labels, not clickable |
| Sidebar Risk/Universe/News links | Shell | Point to `#`, no pages exist |
| ScopeContext universe value | Shell | Hardcoded "US Large Cap" |
| TopBar search | Shell | Visual placeholder only |
| TopBar notifications bell | Shell | Always shows red dot, no backend |
| `fetchScenarioBaseline()` | api.ts | Exported but unused by any page |
| `resolveIncident(id)` | api.ts | Exported but unused by any page |

---

## 4. Phase 4 Implementation Proposal

### Phase 4A — Ingestion Layer

**Purpose:** Add tables and services to acquire, normalize, and store market data and text events.

**New tables (migration 003):**
- `market_bars` — OHLCV data per asset per interval
- `news_events` — text/news items with source, timestamp, sentiment
- `ingestion_manifests` — tracks what was ingested, when, coverage

**New models:**
- `backend/app/models/ingestion.py` — MarketBar, NewsEvent, IngestionManifest

**New schemas:**
- `backend/app/schemas/ingestion.py` — MarketBarSchema, NewsEventSchema, ManifestSchema

**New service:**
- `backend/app/services/ingest.py` — IngestService with methods: `ingest_bars(source, assets, date_range)`, `ingest_news(source, date_range)`, `get_manifest(source)`

**New endpoint:**
- `backend/app/api/v1/ingest.py` — POST /ingest/bars, POST /ingest/news, GET /ingest/status

**Modified:**
- `backend/app/models/__init__.py` — register new models
- `backend/app/schemas/__init__.py` — register new schemas
- `backend/app/api/router.py` — register ingest router
- `backend/seed.py` — add realistic market bar seed data

### Phase 4B — Feature Registry

**Purpose:** Add feature computation and storage layer between raw inputs and engine signals.

**New tables (migration 004):**
- `feature_definitions` — named feature recipes with version
- `feature_sets` — computed feature batches with completeness and freshness

**New models:**
- `backend/app/models/feature.py` — FeatureDefinition, FeatureSet

**New service:**
- `backend/app/services/features.py` — FeatureService with methods: `compute_features(universe_id, as_of)`, `get_feature_set(id)`, `check_freshness()`

**Modified:**
- `backend/app/models/__init__.py`
- `backend/app/schemas/__init__.py`

### Phase 4C — Engine Runner

**Purpose:** Replace seed-only signal data with actual engine execution that reads features and produces signal outputs.

**New service:**
- `backend/app/services/engines.py` — EngineRunner with methods: `run_engine(engine_name, feature_set_id, universe_id)`, `run_all_engines()`
- `backend/app/engines/` — directory with per-engine logic (momentum.py, fundamentals.py, etc.)

**Modified:**
- `backend/app/models/signal.py` — may need additional fields for engine config reference
- `backend/app/api/v1/engines.py` — add POST /engines/run trigger endpoint
- `backend/seed.py` — replace hardcoded engine outputs with engine-produced outputs

### Phase 4D — Decision Pipeline

**Purpose:** Replace seed-only pipeline stages with actual computation that reads signal outputs and produces selection, allocation, timing, risk overlay.

**New service:**
- `backend/app/services/pipeline.py` — PipelineOrchestrator with methods: `run_selection(universe_id, signal_data)`, `run_allocation(selected_assets, signal_data)`, `run_timing(allocation)`, `run_risk_overlay(allocation, constraints)`, `run_full_pipeline()`

**New policy engine:**
- `backend/app/services/policy.py` — PolicyEngine with methods: `evaluate_constraints(portfolio)`, `check_breaches(portfolio)`, `apply_risk_limits()`

**Modified:**
- `backend/app/models/decision_pipeline.py` — may need fields for policy_version reference
- `backend/app/api/v1/decision.py` — ensure stages endpoint reflects computed data
- `backend/seed.py` — pipeline-produced data replaces seed constants

### Phase 4E — Publication Workflow

**Purpose:** Add publication gate logic that evaluates policy, freshness, and operational health before allowing recommendation publication.

**New service:**
- `backend/app/services/publication.py` — PublicationGate with methods: `evaluate_gates(recommendation)`, `publish(recommendation_id)`, `suppress(recommendation_id, reason)`

**New endpoint:**
- POST /api/v1/publication/{id}/publish
- POST /api/v1/publication/{id}/suppress
- GET /api/v1/publication/gates

**Modified:**
- `backend/app/api/v1/actions.py` — integrate with publication gate
- `backend/app/models/recommendation.py` — add publication gate fields
- `backend/app/models/ops.py` — AuditEvent for publication decisions

---

## 5. Verification

### 5.1 Backend Tests

**Command:** `cd backend && python -m pytest tests/ -v`
**Result:** ✅ **45 passed, 1 warning, 0.71s**

```
tests/test_design_sprint2.py    5 passed
tests/test_design_sprint3.py   12 passed
tests/test_design_sprint4.py    9 passed
tests/test_design_sprint5.py    6 passed
tests/test_phase2.py            2 passed
tests/test_phase3.py            3 passed (includes backtests, paper)
tests/test_smoke.py             6 passed
```

Warning: pytest-asyncio event_loop fixture deprecation (non-blocking).

### 5.2 Frontend Build

**Command:** `cd frontend && npx next build`
**Result:** ✅ **Compiled successfully, 10 static pages generated**

```
Route (app)          Size      First Load JS
/                    4.27 kB   94.4 kB
/admin               5.2 kB    95.3 kB
/backtests           4.14 kB   196 kB
/comparison          10 kB     197 kB
/decision            12.1 kB   207 kB
/paper               4.33 kB   192 kB
/replay              2.43 kB   96 kB
```

### 5.3 Overall Verification Summary

| Check | Result |
|---|---|
| Backend starts | **PASS** |
| All 45 tests pass | **PASS** |
| Frontend builds without errors | **PASS** |
| All 7 routes compile | **PASS** |
| No runtime crashes in test suite | **PASS** |
| All claimed DB tables exist in migrations | **PASS** |
| All claimed models match migration tables | **PASS** |
| API router registers all 14 endpoint files | **PASS** |

---

## 6. Summary Assessment

| Area | Status | Detail |
|---|---|---|
| Foundation (FastAPI, DB, migrations) | **PASS** | Solid, functional, deployed to Railway |
| Data contracts (models, schemas) | **PASS** | 21 tables, 22 models, 14 schema files |
| API surface (read endpoints) | **PASS** | 36 endpoints, all return valid JSON |
| Frontend (7 pages, 28 components) | **PASS** | All pages wire to API, build succeeds |
| Tests | **PASS** | 45 tests, all green |
| Ingestion layer | **FAIL** | Does not exist. No market_bars, news_events, manifests |
| Feature registry | **FAIL** | Does not exist. No feature_definitions, feature_sets |
| Engine computation | **FAIL** | Does not exist. Signal outputs are seed-only |
| Pipeline computation | **FAIL** | Does not exist. Pipeline stages are seed-only |
| Publication gates | **FAIL** | Does not exist. No gate evaluation logic |
| Policy engine | **FAIL** | Does not exist. No guardrail evaluation |
| Real data flow end-to-end | **FAIL** | Zero data flows from ingestion through to publication |

**Bottom line:** The platform has a solid foundation, correct data contracts, functional API surface, and polished UI. But it is entirely demo/seed-powered. No data enters the system from real sources, no computation transforms inputs to outputs, and no pipeline connects ingestion to publication. Phase 4 is the transition from demo to real.

---

## 7. Recommended Next Prompt for Phase 4A

```
You are continuing the FINRLX / QuantPipeline project.

Your task is Phase 4A: Ingestion Layer.

Read the Phase 4 Precheck Report at DOCS/handoff/PHASE_4_PRECHECK_REPORT.md first.

Scope:
1. Create migration 003 adding tables: market_bars, news_events, ingestion_manifests
2. Create models: backend/app/models/ingestion.py (MarketBar, NewsEvent, IngestionManifest)
3. Create schemas: backend/app/schemas/ingestion.py
4. Create service: backend/app/services/ingest.py with IngestService
   - ingest_bars(source, assets, date_range) — fetches and stores OHLCV bars
   - ingest_news(source, date_range) — fetches and stores news events
   - get_manifest(source) — returns ingestion status
5. Create endpoints: backend/app/api/v1/ingest.py
   - POST /api/v1/ingest/bars — trigger bar ingestion
   - POST /api/v1/ingest/news — trigger news ingestion
   - GET /api/v1/ingest/status — return manifest/freshness summary
6. Update seed.py to include realistic market_bars for the 10 existing assets (90 days of daily OHLCV)
7. Write tests in backend/tests/test_phase4a.py
8. Do NOT touch frontend in this phase
9. Do NOT refactor existing endpoints

Reference docs:
- Doc 11 Section 6 (Raw and Curated Input Domain)
- Doc 10 Section 8 steps 1-2 (Acquire, normalize, store)
- Doc 12 Section 7 (Reference and Setup Endpoints)

Acceptance criteria:
- Migration runs without error
- Seed creates market_bars data
- GET /ingest/status returns freshness per source
- All existing 45 tests still pass
- New tests pass
- No regressions
```
