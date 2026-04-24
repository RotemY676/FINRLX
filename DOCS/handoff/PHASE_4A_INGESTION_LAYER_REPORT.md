# Phase 4A: Ingestion Layer — Implementation Report

**Date:** 2026-04-24
**Phase:** 4A — Ingestion Layer (first subphase of Backend Pipeline Core)
**Status:** Complete
**Method:** DOCS-driven development per Doc 21 playbook. No frontend changes.

---

## 1. Files Changed

### Created (7)
```
backend/app/models/ingestion.py            — MarketBar, NewsEvent, IngestionManifest models
backend/app/schemas/ingestion.py           — 11 Pydantic schemas for ingestion domain
backend/app/services/ingest.py             — IngestService with deterministic local adapter
backend/app/api/v1/ingest.py               — 4 ingestion endpoints
backend/migrations/versions/003_ingestion_tables.py — migration for 3 new tables
backend/tests/test_phase4a_ingestion.py    — 12 ingestion tests
DOCS/handoff/PHASE_4A_INGESTION_LAYER_REPORT.md
```

### Modified (4)
```
backend/app/models/__init__.py             — registered MarketBar, NewsEvent, IngestionManifest
backend/app/schemas/__init__.py            — registered 11 new schema types
backend/app/api/router.py                  — registered ingest_router
backend/seed.py                            — added 90d bars, 30d news, 2 manifests
backend/tests/conftest.py                  — added ingestion seed for test DB
```

### Not Touched
- No frontend files modified
- No existing endpoints modified
- No existing models modified

---

## 2. Tables Added (migration 003)

| Table | Columns | Purpose |
|---|---|---|
| `market_bars` | id, asset_id, ticker, bar_date, interval, open, high, low, close, volume, source, created_at, updated_at | OHLCV price data per asset per day |
| `news_events` | id, headline, body, source, url, published_at, tickers (JSON), sentiment_score, sentiment_label, category, created_at, updated_at | Text/news items with optional sentiment |
| `ingestion_manifests` | id, source, kind, status, asset_count, row_count, date_from, date_to, started_at, completed_at, error_message, details (JSON), created_at, updated_at | Tracks what was ingested, when, coverage |

**Constraints:**
- `uq_market_bar(asset_id, bar_date, interval)` — prevents duplicate bars
- `ix_market_bar_asset_date` — fast lookup by asset + date
- `ix_news_event_published` — fast lookup by publication time
- `ix_manifest_source` — fast lookup by source

**Total tables:** 24 (was 21)

---

## 3. Endpoints Added (4)

| Method | Path | Purpose | Data Source |
|---|---|---|---|
| POST | `/api/v1/ingest/bars` | Trigger bar ingestion | DB-WRITE via IngestService |
| POST | `/api/v1/ingest/news` | Trigger news ingestion | DB-WRITE via IngestService |
| GET | `/api/v1/ingest/status` | Ingestion freshness per source | DB-READ from manifests + counts |
| GET | `/api/v1/ingest/manifests` | List ingestion manifests | DB-READ |

**Total endpoints:** 40 (was 36)

---

## 4. Tests Added (12)

| Test | What It Verifies |
|---|---|
| `test_market_bar_table_exists` | Seeded bars are queryable via /ingest/status |
| `test_ingestion_manifests_seeded` | Seed conftest creates manifests |
| `test_ingest_status_structure` | Status response has sources, total_bar_count, total_news_count |
| `test_ingest_bars_default` | POST /ingest/bars creates bars + manifest |
| `test_ingest_bars_specific_ticker` | POST /ingest/bars with specific ticker + date range |
| `test_ingest_bars_unknown_ticker` | POST with unknown ticker returns failed manifest |
| `test_ingest_news_default` | POST /ingest/news creates events + manifest |
| `test_ingest_news_date_range` | POST /ingest/news with specific date range |
| `test_manifests_list` | GET /ingest/manifests returns items |
| `test_manifests_filter_by_source` | GET /ingest/manifests?source=test filters correctly |
| `test_status_after_bar_ingestion` | Status reflects newly ingested data |
| `test_repeated_bar_ingestion_creates_new_manifest` | Re-ingestion is idempotent (new manifest, skip duplicate bars) |

---

## 5. Test Command Output

```
$ cd backend && python -m pytest tests/ -v

57 passed, 1 warning in 1.45s

  12 new Phase 4A tests   — all PASS
  45 existing tests        — all PASS (zero regressions)
```

### Seed verification
```
$ rm -f finrlx_dev.db && alembic upgrade head && python -m seed

Running upgrade -> 001_initial
Running upgrade 001_initial -> 002_ops_tables
Running upgrade 002_ops_tables -> 003_ingestion

Seeded: 10 assets, 1 universe, 1 recommendation, 25 signal outputs,
5 evidence items, 8 audit events, 5 replay snapshots, 1 backtest,
1 paper portfolio, 6 data feeds, 3 breaches, 7 queue entries,
2 incidents, 650 market bars (90d × 10 assets), 37 news events (30d),
2 ingestion manifests
```

---

## 6. What Is Now Real

| Component | Status | Detail |
|---|---|---|
| Market bar storage | **REAL** | 3-table schema, unique constraints, queryable |
| News event storage | **REAL** | Schema with sentiment, tickers, category |
| Ingestion manifest tracking | **REAL** | Every ingestion run creates a manifest with status/timing/counts |
| Ingestion status API | **REAL** | Freshness per source, total counts, health classification |
| Idempotent bar ingestion | **REAL** | Duplicate bars are skipped, not inserted twice |
| Deterministic local adapter | **REAL** | Generates repeatable OHLCV + news data from seed |

---

## 7. What Is Still Seed/Mock

| Component | Status | Why |
|---|---|---|
| Local data adapter | **MOCK** | Generates synthetic data from `random.Random(hash(ticker))`, not from real market feeds |
| News sentiment | **MOCK** | Sentiment scores are generated, not from NLP |
| All pre-Phase-4A data | **SEED** | Recommendations, signals, pipeline stages, etc. remain seed-only (out of Phase 4A scope) |

---

## 8. Known Limitations

1. **No real external data providers** — the local adapter generates deterministic synthetic data. Real adapters (Alpha Vantage, Polygon, Reuters) are deferred to a future phase.
2. **No intraday bars** — only daily (`1d`) interval is implemented. The schema supports `1h`, `5m` etc. but the adapter only generates daily.
3. **No news body text** — headlines are generated but body is always null. Real news feeds would populate both.
4. **No incremental ingestion** — each `POST /ingest/bars` generates the full date range. A production adapter would fetch only new bars since last ingestion.
5. **No concurrent ingestion protection** — two simultaneous ingestion calls for the same source could create overlapping manifests. Production would need a lock or job queue.
6. **Bar idempotency uses per-row SELECT** — production would use `INSERT ON CONFLICT` for performance. The current approach is correct but slow for large batches.

---

## 9. Acceptance Criteria

| Criterion | Result |
|---|---|
| Migration 003 runs without error | **PASS** |
| Seed creates market_bars data (650 bars) | **PASS** |
| Seed creates news events (37 events) | **PASS** |
| Seed creates ingestion manifests (2) | **PASS** |
| GET /ingest/status returns freshness per source | **PASS** |
| POST /ingest/bars creates bars and manifest | **PASS** |
| POST /ingest/news creates events and manifest | **PASS** |
| Re-ingestion is idempotent (no duplicate bars) | **PASS** |
| All existing 45 tests still pass | **PASS** |
| 12 new tests pass | **PASS** |
| No frontend changes | **PASS** |
| No unrelated refactor | **PASS** |

---

## Phase 4A.1 Hardening Addendum

**Date:** 2026-04-24

### Changes

1. **Deterministic hash fixed.** Replaced `hash(ticker)` (Python-process-dependent) with `_stable_seed()` using `hashlib.sha256`. The helper returns the same integer for the same inputs across all Python processes, platforms, and versions. Both `_generate_bars` and `_generate_news` now use it.

2. **News idempotency added.** `ingest_news()` now checks for existing rows matching `(source, published_at, headline)` before inserting. Duplicate news events are skipped. The manifest `row_count` reflects only newly inserted rows. Re-ingesting the same source+date range produces `rows_ingested: 0` on the second call.

3. **Failed status visibility added.** `get_status()` no longer filters to only `completed/partial` manifests. All manifests (including `failed` and `running`) are included. Status mapping: `completed` + fresh = `healthy`, `completed` + old = `stale`, `partial` = `partial`, `failed` = `failed`, `running` = `partial`, anything else = `missing`.

4. **Schema clarified.** `SourceFreshness.status` comment updated to list all five possible values: `healthy, stale, partial, failed, missing`.

### Tests Added (3)

| Test | What It Verifies |
|---|---|
| `test_stable_seed_deterministic` | Same inputs → same seed, different inputs → different seed |
| `test_repeated_news_ingestion_is_idempotent` | Second POST /ingest/news over same range inserts 0 new rows |
| `test_failed_ingestion_visible_in_status` | Failed bar ingestion (unknown ticker) shows status=failed in /ingest/status |

### Test Output

```
$ python -m pytest tests/ -v
60 passed, 1 warning in 1.83s

  15 Phase 4A tests (12 original + 3 hardening)
  45 existing tests — all PASS (zero regressions)
```

### Seed Verification

```
$ rm -f finrlx_dev.db && alembic upgrade head && python -m seed
Running upgrade -> 001_initial -> 002_ops_tables -> 003_ingestion
Seeded: 650 market bars, 41 news events, 2 ingestion manifests
```

Note: news event count changed from 37 to 41 because the stable SHA-256 seed produces different random sequences than the previous `hash()`-based seed. This is expected and correct — the data is still deterministic and repeatable.

---

## 10. Recommended Phase 4B Prompt

```
You are continuing the FINRLX / QuantPipeline project.

Your task is Phase 4B: Feature Registry.

Read the Phase 4A report at DOCS/handoff/PHASE_4A_INGESTION_LAYER_REPORT.md first.
Read Doc 11 Section 7 (Feature Registry Domain).
Read Doc 10 Section 8 step 3 (Compute/refresh feature sets).

Scope:
1. Create migration 004 adding tables: feature_definitions, feature_sets
2. Create models: backend/app/models/feature.py (FeatureDefinition, FeatureSet)
3. Create schemas: backend/app/schemas/feature.py
4. Create service: backend/app/services/features.py with FeatureService
   - compute_features(universe_id, as_of) — reads market_bars + news_events, computes features
   - get_feature_set(id) — retrieves computed feature set
   - check_freshness() — returns feature freshness status
5. Create endpoints: backend/app/api/v1/features.py
   - POST /api/v1/features/compute — trigger feature computation
   - GET /api/v1/features/status — feature freshness
   - GET /api/v1/features/{id} — single feature set
6. Implement at least these feature families:
   - Price momentum (returns over 5d, 20d, 60d)
   - Volatility (20d rolling std)
   - Volume profile (relative volume vs 20d avg)
   - News sentiment aggregate (avg sentiment per asset over window)
7. Features must read from market_bars and news_events tables (real DB data)
8. Write tests in backend/tests/test_phase4b_features.py
9. Do NOT touch frontend
10. All existing 57 tests must still pass

Acceptance criteria:
- Feature computation reads real ingested bars and news
- Feature sets are persisted with completeness and freshness metadata
- GET /features/status returns feature freshness
- All existing tests pass + new tests pass
- No frontend changes
```
