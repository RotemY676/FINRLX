# Phase 8C.4: Clean Dependency-Unavailable Path & Fingerprint Preservation Hotfix

**Date:** 2026-04-26
**Status:** Complete

---

## Root Cause

Phase 8C.3 fixed the 500 by adding a try/except fallback around candidate creation in the dependency_unavailable path. However, the primary path still attempted DB writes (RLTrainingRun + RLPolicySnapshot) which failed during autoflush, corrupting the SQLAlchemy session. The fallback caught the exception and rolled back, but:

1. **`production_fingerprints` was missing** — the rollback invalidated the session, so `_capture_production_fingerprints()` in the fallback path couldn't execute read queries.
2. **Raw SQLAlchemy warning leaked** — the except block included `str(e)[:200]` in user-facing warnings, exposing internal text like "This Session's transaction has been rolled back due to a previous exception during flush..."

The underlying DB write failure was caused by non-JSON-serializable types reaching PostgreSQL JSON columns during asyncpg autoflush (the exact type mismatch varies by production data state).

## Chosen Dependency-Unavailable Policy: Option A — No Candidate

**Decision:** When neural dependencies (numpy, torch, gymnasium, stable-baselines3) are unavailable, `train-cpu-prototype` does NOT create any RLTrainingRun or RLPolicySnapshot.

**Rationale:**
- No DB writes = no transaction corruption, ever
- Production fingerprints are captured cleanly via read-only queries
- dependency_unavailable is not a real training result — creating a stub candidate added complexity with no value
- The response is always complete and truthful

**Behavior:**
- `policy_candidate_id: null`
- `training_run_id: null`
- `candidate_isolation_applicable: false`
- `isolation_reason: "No candidate created because neural dependencies are unavailable."`
- `production_fingerprints` always present with full component_checks

## Production Fingerprints Behavior

Always included in the dependency_unavailable response:

```json
{
  "production_fingerprints": {
    "before": { "recommendations_current": {...}, "publication_status": {...}, "overview": {...}, "hash": "..." },
    "after":  { "recommendations_current": {...}, "publication_status": {...}, "overview": {...}, "hash": "..." },
    "unchanged": true,
    "component_checks": {
      "recommendations_current": { "snapshot_available": true, "unchanged": true, ... },
      "publication_status":      { "snapshot_available": true, "unchanged": true, ... },
      "overview":                { "snapshot_available": false, "reason": "..." }
    }
  }
}
```

Fingerprints are captured before and after the (no-op) dependency check. Since no DB writes occur, components are always unchanged.

## Transaction Handling Fix

- dependency_unavailable path performs zero DB writes (no RLTrainingRun, no RLPolicySnapshot)
- Only the audit event is written (via resilient `_create_audit_event` with try/except)
- `db.commit()` only commits the audit event — if that fails, it's logged but doesn't crash
- No session corruption is possible because there are no pending model inserts

## Warning Sanitization

Before (8C.3 fallback):
```
"Candidate creation failed: This Session's transaction has been rolled back..."
```

After (8C.4):
```
"Neural dependencies unavailable: numpy, gymnasium, stable_baselines3, torch."
"No candidate was created."
"No real CPU PPO/A2C training was performed."
```

No raw SQLAlchemy text, no exception strings, no internal state leaked.

## Files Changed

```
backend/app/services/finrlx_research.py     — clean no-candidate dependency_unavailable path
backend/tests/test_phase8c_cpu_prototype.py  — rewritten tests for Option A behavior
DOCS/handoff/PHASE_8C4_DEPENDENCY_UNAVAILABLE_CLEAN_PATH_FINGERPRINT_HOTFIX_REPORT.md
```

## Tests Run

```
375 passed, 2 skipped — zero regressions
```

New/updated tests (30 total in test_phase8c_cpu_prototype.py):
- `test_cpu_prototype_no_candidate_when_deps_unavailable` — Option A: null candidate, isolation not applicable
- `test_cpu_prototype_fingerprints` — production_fingerprints always present
- `test_cpu_prototype_fingerprints_unchanged` — component_checks detail verification
- `test_cpu_prototype_isolation_when_no_candidate` — candidate_isolation_applicable=false, no stale isolation_checks
- `test_dep_unavailable_returns_200` — HTTP 200 confirmed
- `test_dep_unavailable_has_fingerprints` — full fingerprint structure
- `test_dep_unavailable_no_sqlalchemy_warning` — no "transaction"/"rollback"/"flush"/"Session" in warnings
- `test_dep_unavailable_no_candidate_created` — candidate count unchanged
- `test_dep_unavailable_isolation_not_applicable` — candidate_isolation_applicable=false

## Production Smoke Commands

```bash
# The production request — must return 200 with clean response
curl -s -X POST http://localhost:8000/api/v1/rl/finrlx/train-cpu-prototype \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Phase 8C.4 Production Smoke",
    "algorithm": "PPO",
    "start_date": "2026-03-15",
    "end_date": "2026-04-15",
    "timesteps": 50,
    "seed": 42,
    "research_acknowledgement": true
  }' | jq '{
    status: .data.status,
    real_neural_training: .data.real_neural_training,
    candidate_id: .data.policy_candidate_id,
    has_fingerprints: (.data.production_fingerprints != null),
    has_component_checks: (.data.production_fingerprints.component_checks != null),
    unchanged: .data.production_fingerprints.unchanged,
    candidate_isolation_applicable: .data.candidate_isolation_applicable,
    warnings: .data.warnings
  }'

# Expected:
# status: "dependency_unavailable"
# real_neural_training: false
# candidate_id: null
# has_fingerprints: true
# has_component_checks: true
# unchanged: true
# candidate_isolation_applicable: false
# warnings: ["Neural dependencies unavailable: ...", "No candidate was created.", ...]

# Verify no raw transaction text in warnings
curl -s -X POST http://localhost:8000/api/v1/rl/finrlx/train-cpu-prototype \
  -H 'Content-Type: application/json' \
  -d '{"algorithm":"PPO","research_acknowledgement":true}' | jq '.data.warnings[]'

# Other endpoints
curl -s http://localhost:8000/api/v1/health | jq .status
curl -s http://localhost:8000/api/v1/overview | jq .status
curl -s http://localhost:8000/api/v1/recommendations/current | jq .status
curl -s http://localhost:8000/api/v1/publication/status | jq .status
curl -s http://localhost:8000/api/v1/rl/finrlx/dependencies | jq .data.neural_training_available
curl -s -X POST http://localhost:8000/api/v1/rl/finrlx/train-cpu-prototype \
  -H 'Content-Type: application/json' \
  -d '{"algorithm":"PPO","start_date":"bad","research_acknowledgement":true}'
# Expected: 422
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
| No raw SQLAlchemy text in response | CONFIRMED |
| Existing Phase 8A/8B tests pass | CONFIRMED |
| Benchmark regression works | CONFIRMED |

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | train-cpu-prototype returns HTTP 200 | PASS |
| 2 | status="dependency_unavailable" | PASS |
| 3 | real_neural_training=false | PASS |
| 4 | production_fingerprints exists | PASS |
| 5 | production_fingerprints.component_checks exists | PASS |
| 6 | recommendations_current unchanged=true | PASS |
| 7 | publication_status unchanged=true | PASS |
| 8 | overview snapshot_available=false with reason | PASS |
| 9 | No raw SQLAlchemy/transaction warning | PASS |
| 10 | candidate_isolation_applicable=false with reason | PASS |
| 11 | N/A (no candidate in dep-unavailable) | PASS |
| 12 | /rl/execute remains 404 | PASS |
| 13 | /overview works | PASS |
| 14 | /recommendations/current works | PASS |
| 15 | /publication/status works | PASS |
| 16 | benchmark regression works | PASS |
| 17 | backend tests pass (375 passed, 2 skipped) | PASS |
| 18 | no torch/gymnasium/stable-baselines3 installed | PASS |
| 19 | no live RL/broker/recommendation/overview/publication influence | PASS |
