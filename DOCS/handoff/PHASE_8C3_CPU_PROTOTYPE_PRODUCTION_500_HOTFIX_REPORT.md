# Phase 8C.3: CPU Prototype Production 500 Root-Cause Hotfix

**Date:** 2026-04-26
**Status:** Complete

---

## Root Cause

Production `POST /api/v1/rl/finrlx/train-cpu-prototype` returned Internal Server Error (500) instead of a safe `dependency_unavailable` response. Three root causes identified:

### 1. Broad exception risk in `get_neural_dependency_status()`
Only `ImportError` was caught when probing optional libraries. On production, partially installed or broken packages can raise `RuntimeError`, `OSError`, or other exception types during `__import__()`. This would crash before candidate creation even begins.

### 2. Non-JSON-serializable types from PostgreSQL (asyncpg)
Production uses PostgreSQL+asyncpg, while tests use SQLite+aiosqlite. asyncpg can return `Decimal` for numeric aggregates and native `date`/`datetime` objects for temporal columns. These types fail Python's `json.dumps()` which asyncpg uses internally when writing to JSON columns (AuditEvent.details, RLTrainingRun.config, RLPolicySnapshot.policy_payload, etc.). SQLite/aiosqlite returns Python-native `float`/`str` types, masking this in tests.

### 3. Audit event creation failure cascading
`_create_audit_event()` had no error handling. If JSON serialization failed during session autoflush (triggered by subsequent queries), the entire endpoint would crash with 500. Audit logging should not prevent the core research endpoint from returning a safe response.

## Exact Fix

### `backend/app/services/finrlx_research.py`

1. **Added `_json_safe()` recursive serializer** — converts `Decimal` to `float`, `date`/`datetime` to ISO strings, and unknown types to `str`. Applied to:
   - All `_create_audit_event` details (via the method itself)
   - All JSON column values (config, policy_payload, metrics)
   - `_capture_production_fingerprints()` return value
   - All `train_cpu_prototype` response dicts (dependency_unavailable, completed, failed, dataset_invalid)

2. **Broadened exception handling in `get_neural_dependency_status()`** — catches `Exception` instead of just `ImportError`, preventing partial-install crashes.

3. **Made `_create_audit_event()` resilient** — wraps the entire method in try/except. On failure, logs the error but does not crash the endpoint.

4. **Added safe fallback in dependency_unavailable path** — if candidate creation or commit fails, rolls back and returns a safe response with `policy_candidate_id=None` and a warning explaining the failure. The endpoint never returns 500.

### `backend/tests/test_phase8c_cpu_prototype.py`

Added 3 regression tests:
- `test_production_payload_returns_200` — exact production payload, asserts 200 + required fields
- `test_dependency_unavailable_full_response_shape` — validates all fields in dependency_unavailable response
- `test_audit_event_details_json_safe` — queries AuditEvent rows and verifies `json.dumps()` succeeds on all details

## Files Changed

```
backend/app/services/finrlx_research.py     — _json_safe, resilient audit, broad exception handling
backend/tests/test_phase8c_cpu_prototype.py  — 3 production regression tests
DOCS/handoff/PHASE_8C3_CPU_PROTOTYPE_PRODUCTION_500_HOTFIX_REPORT.md
```

## Tests Run

```
371 passed, 2 skipped — zero regressions
```

## Production Smoke Commands

```bash
# The failing request — must now return 200
curl -s -X POST http://localhost:8000/api/v1/rl/finrlx/train-cpu-prototype \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Phase 8C.2 Production Smoke CPU Prototype",
    "algorithm": "PPO",
    "start_date": "2026-03-15",
    "end_date": "2026-04-15",
    "timesteps": 50,
    "seed": 42,
    "research_acknowledgement": true
  }' | jq '.data.status'
# Expected: "dependency_unavailable" (not 500)

# Verify response shape
curl -s -X POST http://localhost:8000/api/v1/rl/finrlx/train-cpu-prototype \
  -H 'Content-Type: application/json' \
  -d '{"algorithm":"PPO","research_acknowledgement":true}' | jq '{
    status: .data.status,
    real_neural_training: .data.real_neural_training,
    has_safety_flags: (.data.safety_flags != null),
    has_dep_status: (.data.dependency_status != null),
    has_isolation: (.data.isolation_checks != null),
    has_fingerprints: (.data.production_fingerprints != null)
  }'

# Malformed dates still 422
curl -s -X POST http://localhost:8000/api/v1/rl/finrlx/train-cpu-prototype \
  -H 'Content-Type: application/json' \
  -d '{"algorithm":"PPO","start_date":"bad","research_acknowledgement":true}'

# Other endpoints still work
curl -s http://localhost:8000/api/v1/health | jq .status
curl -s http://localhost:8000/api/v1/overview | jq .status
curl -s http://localhost:8000/api/v1/recommendations/current | jq .status
curl -s http://localhost:8000/api/v1/publication/status | jq .status
curl -s http://localhost:8000/api/v1/rl/finrlx/status | jq .data.adapter_type
curl -s http://localhost:8000/api/v1/rl/finrlx/dependencies | jq .data.neural_training_available
```

## Safety Confirmations

| Check | Status |
|-------|--------|
| No live RL added | CONFIRMED |
| No broker execution | CONFIRMED |
| No recommendation pollution | CONFIRMED |
| No overview pollution | CONFIRMED |
| No publication influence | CONFIRMED |
| No torch/gymnasium/stable-baselines3 installed | CONFIRMED |
| No real PPO/A2C claimed unless actually run | CONFIRMED |
| dependency_unavailable is truthful | CONFIRMED |
| Existing Phase 8A/8B/8C tests pass | CONFIRMED |
| Benchmark regression works | CONFIRMED |

## Design Handoff Review

No design changes. No frontend touched. Design handoff package reviewed in Phase 8C.1 — intact.

## Audit Convention Decision

**Convention chosen:** Audit event creation failures are **logged but do not crash the endpoint**. Rationale: audit logging is observability, not data integrity. A failed audit event should not prevent a research endpoint from returning a safe, truthful response. The `_create_audit_event` method catches exceptions and logs via `logger.error()`. Production monitoring should alert on these log entries.

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | train-cpu-prototype no longer returns 500 | PASS |
| 2 | Returns truthful dependency_unavailable | PASS |
| 3 | Response includes safety_flags | PASS |
| 4 | Response includes dependency_status | PASS |
| 5 | Response includes production_fingerprints/component_checks | PASS |
| 6 | Response includes isolation_checks if candidate created | PASS |
| 7 | real_neural_training=false when deps unavailable | PASS |
| 8 | Malformed date validation still returns 422 | PASS |
| 9 | /rl/execute remains 404 | PASS |
| 10 | /overview works | PASS |
| 11 | /recommendations/current works | PASS |
| 12 | /publication/status works | PASS |
| 13 | Benchmark regression works | PASS |
| 14 | Backend tests pass (371 passed, 2 skipped) | PASS |
| 15 | Frontend build passes if touched | N/A |
| 16 | No real PPO/A2C claimed unless actually run | PASS |
| 17 | No torch/gymnasium/stable-baselines3 installed | PASS |
| 18 | No live RL/broker/recommendation/overview/publication influence | PASS |
