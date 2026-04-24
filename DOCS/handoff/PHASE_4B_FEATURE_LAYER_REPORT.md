# Phase 4B: Feature Layer — Implementation Report

**Date:** 2026-04-24
**Phase:** 4B — Feature Registry / Feature Layer
**Status:** Complete
**Method:** DOCS-driven development per Doc 21 playbook. No frontend changes.

---

## 1. Files Changed

### Created (6)
```
backend/app/models/feature.py                  — FeatureDefinition, FeatureSet, FeatureValue models
backend/app/schemas/feature.py                 — 7 Pydantic schemas for feature domain
backend/app/services/features.py               — FeatureService with real computation from DB data
backend/app/api/v1/features.py                 — 5 feature endpoints
backend/migrations/versions/004_feature_tables.py — migration for 3 new tables
backend/tests/test_phase4b_features.py         — 12 feature tests
DOCS/handoff/PHASE_4B_FEATURE_LAYER_REPORT.md
```

### Modified (5)
```
backend/app/models/__init__.py     — registered FeatureDefinition, FeatureSet, FeatureValue
backend/app/schemas/__init__.py    — registered 7 new schema types
backend/app/api/router.py          — registered features_router
backend/seed.py                    — ensure_default_definitions + compute one feature set
backend/tests/conftest.py          — 30d bars for 2 assets + 5 news events for test DB
```

---

## 2. Tables Added (migration 004)

| Table | Key Columns | Purpose |
|---|---|---|
| `feature_definitions` | id, key (unique), name, category, description, version, lookback_days, input_kind, output_type, is_active | Named feature recipes |
| `feature_sets` | id, universe_id, as_of, status, feature_version, source_manifest_ids (JSON), asset_count, feature_count, completeness_score, freshness_status, warnings (JSON) | Computed feature batches |
| `feature_values` | id, feature_set_id, asset_id, ticker, feature_key, value, unit, window_days, quality | Individual computed values |

**Total tables:** 27 (was 24)

---

## 3. Endpoints Added (5)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/features/compute` | Trigger feature computation from DB data |
| GET | `/api/v1/features/status` | Feature layer status summary |
| GET | `/api/v1/features/definitions` | List all feature definitions |
| GET | `/api/v1/features/latest` | Latest completed feature set with values |
| GET | `/api/v1/features/{id}` | Single feature set by ID with values |

**Total endpoints:** 45 (was 40)

---

## 4. Feature Definitions (8)

| Key | Category | Lookback | Input | Formula |
|---|---|---|---|---|
| `return_5d` | momentum | 5d | bars | `(close[-1] - close[-6]) / close[-6]` |
| `return_20d` | momentum | 20d | bars | `(close[-1] - close[-21]) / close[-21]` |
| `return_60d` | momentum | 60d | bars | `(close[-1] - close[-61]) / close[-61]` |
| `volatility_20d` | volatility | 20d | bars | `std(daily_returns[-20:]) * sqrt(252)` annualised |
| `drawdown_20d` | drawdown | 20d | bars | `max(peak_to_trough) / peak` over 20d window (negative) |
| `relative_volume_20d` | volume | 20d | bars | `volume[-1] / mean(volume[-20:])` |
| `news_sentiment_7d` | sentiment | 7d | news | `mean(sentiment_score)` for ticker over 7 calendar days |
| `news_count_7d` | sentiment | 7d | news | `count(news_events)` for ticker over 7 calendar days |

---

## 5. Tests Added (12)

| Test | What It Verifies |
|---|---|
| `test_feature_definitions_exist` | GET /definitions returns 8+ definitions with expected keys |
| `test_feature_definition_structure` | Each definition has key, name, category, lookback_days, input_kind |
| `test_compute_features` | POST /compute creates feature set with values |
| `test_compute_reads_market_bars` | return_5d has quality=ok (reads real bars from DB) |
| `test_compute_reads_news_events` | news_sentiment_7d has quality=ok for AAPL (reads real news from DB) |
| `test_insufficient_data_truthful` | Computing at 2020-01-10 (no data) → quality=insufficient_data |
| `test_feature_status` | GET /status returns definition counts and latest set |
| `test_get_latest_feature_set` | GET /latest returns set with values |
| `test_get_feature_set_by_id` | GET /{id} returns correct set |
| `test_get_feature_set_not_found` | GET /nonexistent returns 404 |
| `test_completeness_below_one_with_no_data` | No data → completeness < 1.0 |
| `test_warnings_list_insufficient` | Warnings mention "insufficient" for missing data |

---

## 6. Test Output

```
$ python -m pytest tests/ -v
72 passed, 1 warning in 2.30s

  12 new Phase 4B tests    — all PASS
  60 existing tests         — all PASS (zero regressions)
```

### Seed Verification

```
$ rm -f finrlx_dev.db && alembic upgrade head && python -m seed

Running upgrade -> 001_initial -> 002_ops_tables -> 003_ingestion -> 004_feature

Seeded: 10 assets, 650 market bars, 41 news events, 2 ingestion manifests,
1 feature set (80 values, completeness 90%)
```

---

## 7. What Is Now Real

| Component | Status | Detail |
|---|---|---|
| Feature definitions | **REAL** | 8 definitions persisted in DB, queryable, versioned |
| Feature computation | **REAL** | Reads market_bars + news_events from DB, computes actual values |
| Price momentum | **REAL** | return_5d, return_20d, return_60d from actual close prices |
| Volatility | **REAL** | volatility_20d from actual daily returns |
| Drawdown | **REAL** | drawdown_20d from actual peak-to-trough |
| Volume profile | **REAL** | relative_volume_20d from actual volume data |
| News sentiment | **REAL** | news_sentiment_7d and news_count_7d from actual news events |
| Completeness tracking | **REAL** | Truthful completeness_score + freshness_status |
| Insufficient data handling | **REAL** | quality=insufficient_data, not faked |
| Feature lineage | **REAL** | source_manifest_ids links to ingestion manifests |

---

## 8. What Is Still Seed/Mock

| Component | Status |
|---|---|
| Market bar data | Deterministic local adapter (not real market feeds) |
| News event data | Deterministic local adapter (not real news providers) |
| All pre-Phase-4A data | Seed-only (recommendations, signals, pipeline stages) |
| Engine outputs | Still seed-only (Phase 4C scope) |
| Recommendations | Still seed-only (Phase 4D scope) |

---

## 9. Known Limitations

1. **News sentiment query** uses Python-side filtering for SQLite JSON compatibility. Postgres-native `@>` would be more efficient.
2. **No feature caching** — each computation recomputes all values. Future: skip assets whose bars haven't changed.
3. **No partial feature set** — if one asset fails, the whole set still completes with reduced completeness. No per-asset retry.
4. **Feature definitions are static** — no UI for adding/editing definitions yet.
5. **No feature drift detection** — comparing consecutive feature sets for anomaly detection is deferred.
6. **Seed idempotency** — re-running seed skips feature computation if a set already exists, but doesn't update if definitions change.

---

## Phase 4B.1 Hardening Addendum

**Date:** 2026-04-24

### Changes

1. **news_count_7d zero-count semantics fixed.** Split `_get_news_sentiment()` into `_query_ticker_news()` (shared query), `_get_news_sentiment()` (mean, insufficient_data on zero), and `_get_news_count()` (count, ok on zero when source exists, insufficient_data when no source). Zero news for a ticker is now `value=0.0, quality=ok` — not penalised.

2. **Warning quality improved.** News features no longer produce misleading "have Xd bars" warnings. New format: `"{ticker}/news_sentiment_7d: no ticker-specific news in 7d window"`.

3. **Completeness score improved.** Seed completeness rose from 90% to 95% because `news_count_7d=0` no longer reduces it.

### Tests Added (4)

| Test | What It Verifies |
|---|---|
| `test_news_count_zero_is_ok` | news_count_7d value=0.0 quality=ok when news source exists |
| `test_news_sentiment_missing_when_no_source` | news_sentiment_7d value=None quality=insufficient_data when no source |
| `test_news_count_source_missing_is_insufficient` | news_count_7d quality=insufficient_data when no news source at all |
| `test_ensure_default_definitions_idempotent` | Default definition keys are unique; re-running ensure is safe |

### Test Output

```
$ python -m pytest tests/ -v
76 passed, 1 warning in 2.69s

  16 Phase 4B tests (12 original + 4 hardening)
  60 existing tests — all PASS (zero regressions)
```

### Seed Verification

```
$ rm -f finrlx_dev.db && alembic upgrade head && python -m seed
1 feature set (80 values, completeness 95%)
```

---

## 10. Recommended Phase 4C Prompt

```
You are continuing the FINRLX / QuantPipeline project.

Your task is Phase 4C: Engine Runner.

Read the Phase 4B report at DOCS/handoff/PHASE_4B_FEATURE_LAYER_REPORT.md first.
Read Doc 10 Section 8 step 4 (Run engine-level signals).
Read Doc 11 Section 8 (Signal and Engine Output Domain).

Scope:
1. Create service: backend/app/services/engine_runner.py
   - EngineRunner with run_engine(engine_name, feature_set_id) and run_all_engines()
2. Create per-engine modules: backend/app/engines/
   - momentum.py — reads return_5d, return_20d, return_60d, volatility_20d
   - fundamentals.py — reads return_20d, relative_volume_20d
   - sentiment.py — reads news_sentiment_7d, news_count_7d
   - Each engine produces SignalOutput rows with stance, confidence, rationale
3. Add endpoint: POST /api/v1/engines/run
4. Engines must read from the feature_values table (real computed features)
5. Engine outputs must be persisted as SignalRun + SignalOutput rows
6. Write tests in backend/tests/test_phase4c_engines.py
7. Do NOT touch frontend
8. All existing 72 tests must still pass

Acceptance criteria:
- Engines read real feature values from DB
- Engine outputs are persisted and queryable
- POST /engines/run triggers all engines and returns results
- All existing tests pass + new tests pass
```
