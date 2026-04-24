# Phase 4C: Engine Runner — Implementation Report

**Date:** 2026-04-24
**Phase:** 4C — Engine Runner
**Status:** Complete
**Method:** DOCS-driven development per Doc 21 playbook. No frontend changes.

---

## 1. Files Changed

### Created (5)
```
backend/app/models/engine.py                   — EngineDefinition model
backend/app/services/engines.py                — EngineService + 3 engine implementations
backend/migrations/versions/005_engine_registry.py — engine_definitions table + feature_set_id on signal_runs
backend/tests/test_phase4c_engines.py          — 12 engine tests
DOCS/handoff/PHASE_4C_ENGINE_RUNNER_REPORT.md
```

### Modified (6)
```
backend/app/models/signal.py       — added feature_set_id to SignalRun
backend/app/models/__init__.py     — registered EngineDefinition
backend/app/schemas/engine.py      — rewritten: EngineDefinitionResponse, EngineSignalDetail, EngineRunRequest/Result/Response, EngineStatusResponse
backend/app/schemas/__init__.py    — registered new schema types
backend/app/api/v1/engines.py      — rewritten: 6 new endpoints + 3 backward-compatible endpoints using real DB signals
backend/seed.py                    — ensure engine definitions + run engines after feature set
backend/tests/conftest.py          — added EngineDefinition import
backend/tests/test_design_sprint2.py — relaxed evidence item count assertion (was hardcoded to 5)
```

---

## 2. Tables Added / Modified

| Table | Change | Purpose |
|---|---|---|
| `engine_definitions` | **NEW** (migration 005) | Persistent engine registry: key, name, category, required_feature_keys, is_active |
| `signal_runs` | **MODIFIED** — added `feature_set_id` column | Lineage: which feature set was used for each run |

**Total tables:** 28 (was 27)

---

## 3. Endpoints Added / Modified

| Method | Path | Change | Status |
|---|---|---|---|
| POST | `/engines/run` | **NEW** | Triggers real engine execution from feature values |
| GET | `/engines/latest-signals` | **NEW** | Returns latest persisted signal outputs with full detail |
| GET | `/engines/status` | **NEW** | Engine layer status summary |
| GET | `/engines/definitions` | **NEW** | Lists engine definitions from DB |
| GET | `/engines/comparison` | **REWRITTEN** | Now reads real signal_outputs instead of ENGINE_DEFS |
| GET | `/engines/disagreement` | **REWRITTEN** | Now computes from real signal stances, not hardcoded 0.37 |
| GET | `/engines/evidence` | **REWRITTEN** | Derives evidence from real signals; legacy fallback if no signals |

**Total endpoints:** 49 (was 45)

---

## 4. Engine Definitions (3 active)

| Key | Category | Required Features | Description |
|---|---|---|---|
| `technical_momentum` | momentum | return_5d, return_20d, return_60d, volatility_20d, drawdown_20d | Price momentum penalised by volatility and drawdown |
| `risk_quality` | risk | volatility_20d, drawdown_20d, relative_volume_20d | Risk scoring: lower vol/dd = higher score |
| `news_sentiment` | sentiment | news_sentiment_7d, news_count_7d | News-driven stance from aggregated sentiment |

---

## 5. Engine Formulas

### technical_momentum
```
raw = 0.25 * norm(return_5d/0.20) + 0.40 * norm(return_20d/0.20) + 0.35 * norm(return_60d/0.20)
vol_penalty = min(vol_20d / 0.40, 1) * 0.15
dd_penalty  = min(|dd_20d| / 0.10, 1) * 0.10
score = clamp(raw - vol_penalty - dd_penalty, -1, 1)
stance: score >= 0.35 → buy, score <= -0.25 → sell, otherwise hold
confidence: 0.3 + (ok_features * 0.15) + vol_bonus + dd_bonus
```

### risk_quality
```
vol_score = 1.0 - clamp(vol_20d / 0.50, 0, 1)
dd_score  = 1.0 - clamp(|dd_20d| / 0.15, 0, 1)
vol_profile = clamp(relative_volume / 2.0, 0, 1)
score = (0.45 * vol_score + 0.35 * dd_score + 0.20 * vol_profile) * 2 - 1
stance: score <= -0.30 → trim, score <= -0.10 → sell, otherwise hold
```

### news_sentiment
```
if news_count_7d == 0 and source exists: score=0, confidence=0.25, stance=hold, caveat
if news source unavailable: score=0, confidence=0.10, stance=hold, caveat
otherwise: score = clamp(sentiment_7d * 1.5, -1, 1)
confidence = 0.20 + news_count * 0.05
stance: score >= 0.30 → buy, score <= -0.30 → sell, otherwise hold
```

---

## 6. Feature Lineage

Each `signal_run` now stores `feature_set_id` linking to the feature set used.
Each `signal_output.artifacts` stores `source_feature_set_id` and `feature_quality` for per-asset lineage.

Data flow: `market_bars` → `feature_values` → `signal_outputs`

---

## 7. Insufficient Data Handling

- If all required features are `insufficient_data`, engine returns `score=0, confidence=0.1, stance=hold, caveat="No [type] data available"`.
- If some features are missing, confidence is reduced proportionally and caveats list the gaps.
- `news_count_7d=0` with source available → `hold` with caveat, not failure.
- `news_count_7d` missing (no source) → degraded caveat.

---

## 8. Hardcoded ENGINE_DEFS Removal

| Before | After |
|---|---|
| `from seed import ENGINE_DEFS` in engines.py | Removed. No import from seed. |
| Comparison endpoint mapped through ENGINE_DEFS | Reads real SignalOutput from DB |
| Disagreement dispersion = 0.37 literal | Computed from actual engine stance counts |
| Evidence items = EVIDENCE_ITEMS constant | Derived from real signal output artifacts |

Legacy `ENGINE_DEFS` constant still exists in `seed.py` for backward compatibility with the old seed signal outputs (pre-Phase-4C), but it is no longer the runtime source of truth for any endpoint.

---

## 9. Tests Added (12)

| Test | What It Verifies |
|---|---|
| `test_engine_definitions_exist` | GET /definitions returns 3+ definitions |
| `test_engine_definition_structure` | Required fields present |
| `test_run_engines` | POST /engines/run creates signals from features |
| `test_engine_uses_feature_values` | Signals have feature_set lineage |
| `test_technical_momentum_non_hardcoded` | Different assets get different scores |
| `test_news_sentiment_zero_count_hold` | Zero news → hold, not error |
| `test_insufficient_data_produces_caveats` | No data → caveats, not fake confidence |
| `test_latest_signals_endpoint` | GET /latest-signals returns persisted outputs |
| `test_engine_status` | GET /status returns summary |
| `test_comparison_uses_real_signals` | Comparison uses real engine keys |
| `test_disagreement_uses_real_signals` | Dispersion computed, not hardcoded |
| `test_evidence_not_hardcoded` | Evidence derives from real engine names |

---

## 10. Test Output

```
$ python -m pytest tests/ -v
88 passed, 1 warning in 3.40s

  12 new Phase 4C tests   — all PASS
  76 existing tests        — all PASS (1 updated assertion, zero regressions)
```

### Seed Verification

```
$ rm -f finrlx_dev.db && alembic upgrade head && python -m seed
5 migrations OK
Seeded: 650 market bars, 41 news, 80 features (95%), 3 engines ran, 30 signals produced
```

---

## 11. What Is Now Real

| Layer | Status |
|---|---|
| Ingestion → DB | **REAL** (deterministic local adapter) |
| DB → Features | **REAL** (computed from market_bars + news_events) |
| Features → Signals | **REAL** (3 engines read feature_values, write signal_outputs) |
| Signal endpoints | **REAL** (comparison/disagreement/evidence from DB signals) |
| Engine lineage | **REAL** (signal_run.feature_set_id + artifacts.source_feature_set_id) |

---

## 12. What Remains Seeded/Demo

| Component | Status |
|---|---|
| Market bar data | Deterministic local adapter (not real market feeds) |
| News event data | Deterministic local adapter (not real news providers) |
| Recommendations | Still seed-only (Phase 4D scope) |
| Decision pipeline | Still seed-only (Phase 4D scope) |
| Publication workflow | Still seed-only (Phase 4E scope) |
| Old seed signal outputs | Still exist in DB from seed.py (ENGINE_DEFS block); **isolated** — filtered out by registry-aware queries |

---

## 13. Known Limitations

1. **No ML/RL engines** — all 3 engines are deterministic analytical functions. RL/FINRL-X is not implemented.
2. **Engine weight is equal** (1/3 each) — no learned or configured engine weighting yet.
3. **Horizon is fixed at "3M"** — engines don't compute their own horizon.
4. **No engine versioning in runs** — all engines are v1; version comparison is deferred.
5. **Old seed ENGINE_DEFS block** still creates 5 old-format signal runs during seed. These remain in the DB but are filtered out by `get_latest_signals(registered_only=True)`.
6. **Evidence endpoint** produces structured items from signal artifacts, not a full NLP narrative.

---

## Phase 4C.1 Hardening Addendum

**Date:** 2026-04-24

### Changes

1. **Legacy seeded signal isolation.** `get_latest_signals(registered_only=True)` now filters to only active `EngineDefinition.key` values. Legacy seeded runs (momentum, fundamentals, narrative, riskparity, flow) are excluded from all endpoints. No "unknown" engine_key appears.

2. **Run list/detail endpoints added.**
   - `GET /engines/runs` — lists recent signal runs with output counts
   - `GET /engines/runs/{run_id}` — single run detail with signal count
   - `EngineRunDetailResponse` schema added.

3. **Actual feature_set_id in run response.** `POST /engines/run` now returns the resolved `feature_set_id` from the engine results, not the (possibly null) request input.

4. **Report corrected.** "Old seed signal outputs are not used by any endpoint" → "filtered out by registry-aware queries".

### Tests Added (7)

| Test | What It Verifies |
|---|---|
| `test_latest_signals_excludes_legacy` | No legacy keys (momentum, fundamentals, etc.) in latest-signals |
| `test_no_unknown_engine_key` | No engine_key="unknown" in latest-signals |
| `test_comparison_only_registered` | Comparison includes only registered keys |
| `test_disagreement_only_registered` | Disagreement counts only registered engines |
| `test_engine_runs_list` | GET /engines/runs returns runs with signal_count |
| `test_engine_run_detail` | GET /engines/runs/{id} returns single run |
| `test_engine_run_returns_feature_set_id` | POST /engines/run returns actual feature_set_id |

### Test Output

```
$ python -m pytest tests/ -v
95 passed, 1 warning in 3.95s

  19 Phase 4C tests (12 original + 7 hardening)
  76 existing tests — all PASS (zero regressions)
```

---

## Phase 4C.2 Cleanup Addendum

**Date:** 2026-04-24

### Changes

1. **Removed legacy evidence fallback.** The `from seed import EVIDENCE_ITEMS` fallback in `/engines/evidence` is removed. When no registered engine signals exist, the endpoint returns `data=None` with warning `"No engine-derived evidence available. Run /api/v1/engines/run first."`.

2. **No seed.py import in runtime engines.py.** The word `EVIDENCE_ITEMS` no longer appears in the engines endpoint source code. No `from seed import` statement exists.

3. **Sprint 2 test updated.** `test_evidence` now accepts `data=None` when no engine run has happened (no legacy fallback to mask this).

### Tests Added (2)

| Test | What It Verifies |
|---|---|
| `test_no_seed_import_in_engines_endpoint` | Source code contains no `from seed import` or `EVIDENCE_ITEMS` |
| `test_evidence_no_signals_returns_none` | Without signals: data=None + warning; with signals: real engine sources only |

### Test Output

```
$ python -m pytest tests/ -v
97 passed, 1 warning in 4.20s

  21 Phase 4C tests (12 original + 7 hardening + 2 cleanup)
  76 existing tests — all PASS (zero regressions)
```

---

## 14. Recommended Phase 4D Prompt

```
You are continuing the FINRLX / QuantPipeline project.

Your task is Phase 4D: Decision Pipeline.

Read the Phase 4C report at DOCS/handoff/PHASE_4C_ENGINE_RUNNER_REPORT.md first.
Read Doc 10 Section 8 steps 5-8 (Selection → Allocation → Timing → Risk Overlay).
Read Doc 11 Section 9 (Decision Pipeline Domain).

Scope:
1. Create service: backend/app/services/pipeline.py with PipelineOrchestrator
   - run_selection(universe_id, signal_data)
   - run_allocation(selected_assets, signal_data)
   - run_timing(allocation)
   - run_risk_overlay(allocation, constraints)
   - run_full_pipeline() — orchestrates the complete flow
2. Each stage reads real signal_outputs from DB (produced by Phase 4C engines)
3. Each stage writes to its existing table (selection_runs, allocation_results, etc.)
4. The pipeline produces a new Recommendation with real computed weights
5. Add endpoint: POST /api/v1/pipeline/run
6. Write tests in backend/tests/test_phase4d_pipeline.py
7. Do NOT touch frontend
8. All existing 88 tests must still pass

Acceptance criteria:
- Pipeline reads real signal_outputs
- Pipeline writes real selection/allocation/timing/risk overlay records
- Pipeline produces a real Recommendation with computed weights
- All existing tests pass + new tests pass
```
