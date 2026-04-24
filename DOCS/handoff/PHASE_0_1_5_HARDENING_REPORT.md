# Phase 0+1.5 Hardening Report

**Date:** 2026-04-24
**Phase:** Foundation Hardening and Verification
**Status:** Complete

---

## 1. What Was Hardened

### Repo Cleanup
- Removed PyCharm placeholder `main.py` from project root
- Untracked `.idea/` directory from git (6 files)
- Untracked 4 ZIP archives from git (QuantPipeline_Claude_Design_Pack.zip, QuantPipeline_Docs_01_15_Package.zip, QuantPipeline_Docs_16_20_Package.zip, DOCS/source_packages/QuantPipeline_Docs_01_24_Package.zip)
- Updated `.gitignore` to cover: `*.zip`, `*.db`, `*.log`, `logs/*`, `design/exports/*`
- Extracted docs under `DOCS/source_packages/` remain intact and tracked

### Alembic Migration
- Created first real migration: `migrations/versions/001_initial_schema.py`
- Migration covers all 18 tables across 6 data domains
- Includes both `upgrade()` and `downgrade()` functions
- Removed `Base.metadata.create_all` from seed script — migrations are now the source of truth
- Seed script now requires `alembic upgrade head` to be run first

### Database Configuration
- Changed default `DATABASE_URL` to `sqlite+aiosqlite:///./finrlx_dev.db` for zero-friction local dev
- PostgreSQL remains the production target (set via `DATABASE_URL` env var)
- Added `aiosqlite` to requirements.txt
- Docker Compose still uses PostgreSQL with `asyncpg`

### Docker Compose
- Backend startup command now runs `alembic upgrade head && python -m seed` before starting uvicorn
- Seed is idempotent so this is safe on repeated `docker compose up`

### Test Layer
- Added `tests/conftest.py` with in-memory SQLite test fixtures and seeded test data
- Added `tests/test_smoke.py` with 6 smoke tests
- Added `pytest.ini` with async mode configuration
- Added `pytest`, `pytest-asyncio`, `anyio` to requirements.txt

### Documentation
- Updated `PHASE_0_1_RUNBOOK.md` with correct local dev flow (SQLite default, migration-first)
- Updated `PHASE_0_1_IMPLEMENTATION_REPORT.md` to reflect resolved gaps
- Updated `backend/.env.example` with SQLite default and PostgreSQL instructions

---

## 2. What Was Verified by Actual Execution

| Check | Method | Result |
|---|---|---|
| Migration upgrade (18 tables) | `alembic upgrade head` against SQLite | **PASS** — 18 tables created |
| Migration downgrade | `alembic downgrade base` | **PASS** — all tables dropped cleanly |
| Migration re-upgrade | `alembic upgrade head` after downgrade | **PASS** — idempotent |
| Seed script | `python -m seed` after migration | **PASS** — 10 assets, 1 universe, 1 recommendation |
| Backend startup | `uvicorn app.main:app` | **PASS** — starts on port 8877 |
| `GET /health` | httpx request to running server | **PASS** — `{"status": "ok", "version": "0.1.0"}` |
| `GET /api/v1/health` | httpx request to running server | **PASS** — `status=ok, database=connected` |
| `GET /api/v1/overview` | httpx request to running server | **PASS** — returns published recommendation with 10 positions, confidence triplet (0.78/0.92/0.95), 1 warning |
| `GET /api/v1/recommendations/current` | httpx request to running server | **PASS** — returns 10 weights (AAPL 15% overweight, MSFT 14%, etc.), rationale, warnings |
| `GET /docs` | httpx request to running server | **PASS** — Swagger UI serves |
| Smoke tests (6 tests) | `python -m pytest tests/ -v` | **PASS** — 6/6 passed in 0.40s |
| Frontend build | `npx next build` | **PASS** — 7 routes compiled, 0 errors |
| Python schema imports | All 13 Pydantic schemas + 18 SQLAlchemy models | **PASS** |
| docker-compose.yml validity | YAML parse | **PASS** — 3 services |

---

## 3. What Still Remains Unverified

| Item | Reason | Risk |
|---|---|---|
| Frontend browser rendering | Cannot open a browser from this environment | Low — build succeeds, components are structurally correct |
| Frontend-to-backend data flow in browser | Requires both services running + browser | Medium — proxy is configured in next.config.js, API client matches backend schemas |
| Docker Compose full startup | Docker not available in this environment | Low — YAML is valid, Dockerfiles are standard, startup command is tested logic |
| PostgreSQL-specific migration | Only tested with SQLite | Low — migration uses standard SQLAlchemy ops, no PG-specific features |

**Honest statement:** I have not seen the Overview page render in a browser. I verified the backend serves correct data, the frontend compiles cleanly, and the API client types match the backend schemas. The visual rendering requires manual browser verification.

---

## 4. What Was Cleaned from the Repo

| Item | Action |
|---|---|
| `main.py` (root) | Deleted — was PyCharm template |
| `.idea/` (6 files) | Untracked from git via `git rm --cached` |
| `QuantPipeline_Claude_Design_Pack.zip` | Untracked from git (file remains on disk) |
| `QuantPipeline_Docs_01_15_Package.zip` | Untracked from git (file remains on disk) |
| `QuantPipeline_Docs_16_20_Package.zip` | Untracked from git (file remains on disk) |
| `DOCS/source_packages/...Package.zip` | Untracked from git (file remains on disk) |
| `test_migration.db` | Removed (test artifact) |

---

## 5. Migration Created

**File:** `backend/migrations/versions/001_initial_schema.py`

**Revision:** `001_initial`

**Tables (18):**

| Domain | Tables |
|---|---|
| Reference Data | assets, universes, universe_memberships, benchmarks |
| Signals | signal_runs, signal_outputs |
| Decision Pipeline | selection_runs, allocation_results, timing_results, risk_overlay_results |
| Recommendation | recommendations, recommendation_weights |
| Validation | backtest_experiments, paper_portfolios, replay_snapshots |
| Admin/Ops | audit_events, incidents, system_health_snapshots |

**Verified:** upgrade, downgrade, re-upgrade all work correctly.

---

## 6. Tests Added

**File:** `backend/tests/test_smoke.py` (6 tests)

| Test | What It Verifies |
|---|---|
| `test_root_health` | `GET /health` returns 200 with status and version |
| `test_api_v1_health` | `GET /api/v1/health` returns ok with DB connected |
| `test_overview` | `GET /api/v1/overview` returns seeded recommendation with correct confidence triplet and position count |
| `test_current_recommendation` | `GET /api/v1/recommendations/current` returns weights with correct tickers, weights, and stances |
| `test_recommendation_by_id_not_found` | `GET /api/v1/recommendations/{bad_id}` returns 404 |
| `test_overview_envelope_structure` | Response envelope matches doc 12 contract (meta.api_version, meta.generated_at, meta.warnings) |

**Test infrastructure:**
- In-memory SQLite with async session
- Test fixtures seed 2 assets + 1 recommendation with 2 weights
- Uses `httpx.AsyncClient` with ASGI transport (no network needed)
- All 6 tests pass in 0.40s

---

## 7. What Still Blocks Phase 2

**Nothing blocks Phase 2.** The foundation is verified and trustworthy:
- Schema is stable (18 tables matching doc 11)
- API contracts are stable (13 Pydantic schemas matching doc 12)
- Backend serves real data from a real database
- Frontend builds and has the correct shell structure
- Tests cover the critical API paths
- Migration provides reproducible schema creation

**Recommended before starting Phase 2:**
1. Manual browser verification of the Overview page (5 minutes)
2. Decide whether to install a charting library now or during Phase 2
3. Consider adding a `Makefile` or `scripts/dev.sh` for common commands

---

## Files Created

```
backend/migrations/versions/001_initial_schema.py
backend/tests/__init__.py
backend/tests/conftest.py
backend/tests/test_smoke.py
backend/pytest.ini
DOCS/handoff/PHASE_0_1_5_HARDENING_REPORT.md
```

## Files Modified

```
.gitignore                                   — added *.zip, *.db, expanded coverage
backend/.env.example                         — updated for SQLite default
backend/app/core/config.py                   — default to SQLite for local dev
backend/requirements.txt                     — added aiosqlite, pytest, pytest-asyncio, anyio
backend/seed.py                              — removed create_all, requires migration first
docker-compose.yml                           — backend runs migrations+seed before start
DOCS/handoff/PHASE_0_1_IMPLEMENTATION_REPORT.md — updated known gaps
DOCS/handoff/PHASE_0_1_RUNBOOK.md            — rewritten for current flow
```

## Files Deleted

```
main.py                                      — PyCharm placeholder removed
```

## Files Untracked from Git (still on disk)

```
.idea/ (6 files)
QuantPipeline_Claude_Design_Pack.zip
QuantPipeline_Docs_01_15_Package.zip
QuantPipeline_Docs_16_20_Package.zip
DOCS/source_packages/QuantPipeline_Docs_01_24_Package.zip
```
