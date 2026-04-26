# Phase 8E: Research Artifact Import & Validation

**Date:** 2026-04-26
**Status:** Complete

---

## Executive Summary

Phase 8E adds a safe backend path to import local CPU PPO/A2C research artifacts (produced by Phase 8D) as shadow-only research candidates. Artifacts are validated against a strict schema enforcing all safety flags before import. Imported candidates are isolated from production — no promotion, publication, recommendation, overview, or broker influence.

## Files Changed

```
EDIT backend/app/services/finrlx_research.py   — validate_research_artifact(), import_research_artifact(), _compute_artifact_hash()
EDIT backend/app/api/v1/rl_finrlx.py           — 2 new endpoints + 2 request models
NEW  backend/tests/test_phase8e_artifact_import.py — 23 tests
NEW  DOCS/handoff/PHASE_8E_RESEARCH_ARTIFACT_IMPORT_VALIDATION_REPORT.md
```

No frontend changes. No production dependency changes. No migration needed (uses existing RLPolicySnapshot table).

## Backend Changes

### Service: `FinRLXResearchService`

**`validate_research_artifact(artifact: dict) -> dict`** (static method)
- Validates 19 required fields
- Hard-rejects unsafe safety flag values (live_pipeline_influence=true, no_broker_execution=false, etc.)
- Validates algorithm in {PPO, A2C}
- Checks type consistency (booleans, dicts, lists)
- Checks training metadata consistency (if real_neural_training=true, expects timesteps/algorithm/seed)
- Checks synthetic data labeling consistency
- Computes deterministic artifact_hash (SHA-256)
- Returns: `{valid, errors, warnings, artifact_hash, normalized_artifact_summary, safety_flags}`

**`import_research_artifact(artifact, source, notes) -> dict`** (async)
- Validates artifact first
- If invalid: creates `finrlx_research_artifact_import_rejected` audit event, returns rejected status
- If valid: captures pre-import production fingerprints, creates `RLPolicySnapshot` with `policy_type=finrlx_cpu_{algo}_research_import`, captures post-import fingerprints, creates audit events, returns full import result with isolation checks

**`_compute_artifact_hash(artifact: dict) -> str`** (static)
- Deterministic SHA-256 of artifact (sorted keys, excluding `artifact_created_at`)
- Returns 32-char hex digest

## API Endpoints Added

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/rl/finrlx/validate-research-artifact` | POST | Validate artifact schema without importing |
| `/api/v1/rl/finrlx/import-research-artifact` | POST | Validate + import as shadow candidate |

### Request models

**`FinRLXValidateArtifactRequest`**: `{artifact: dict}`

**`FinRLXImportArtifactRequest`**: `{artifact: dict, import_acknowledgement: bool, source: str, notes: str | None}`

## Frontend/UI Changes

**None.** No import/upload UI pattern exists in the design handoff. UI deferred to Phase 8F.

## Design Handoff Review

**Files reviewed:** HANDOFF.md, Ops.html, Backtests.html, Design System.html, styles.css, tokens.css, ops.css, backtests.css

**UI touched:** No.

**Why reviewed:** Confirmed no existing import/upload/artifact-ingest UI patterns exist in the design system. The ops audit timeline pattern and status pills are suitable for future artifact import UI (Phase 8F). No new design system needed.

## Artifact Validation Behavior

Rejects artifacts that:
- Miss any of 19 required fields
- Have wrong `artifact_type` (must be `finrlx_cpu_rl_research_artifact`)
- Have unsafe safety flags (`live_pipeline_influence=true`, `no_broker_execution=false`, etc.)
- Have invalid algorithm (not PPO or A2C)
- Have wrong types (non-boolean for `real_neural_training`, non-dict for `training_config`, etc.)

Warns (but accepts) artifacts that:
- Claim `real_neural_training=true` but lack timesteps/algorithm/seed in training_config
- Claim `synthetic_data=true` but don't label it in dataset_summary or warnings

## Import Behavior

1. Requires `import_acknowledgement=true` (HTTP 422 otherwise)
2. Validates artifact schema (422 with errors if invalid)
3. Creates `RLPolicySnapshot` with:
   - `policy_type`: `finrlx_cpu_ppo_research_import` or `finrlx_cpu_a2c_research_import`
   - `policy_payload`: includes artifact hash, summary, safety flags, source, notes
   - `metrics`: copied from artifact `training_metrics`
4. No `RLTrainingRun` created (artifact was trained locally, not on backend)
5. Returns full isolation checks, production fingerprints, and validation result

## Artifact Hash Behavior

- SHA-256 of stable artifact content (sorted keys, `default=str`)
- Excludes `artifact_created_at` (volatile timestamp)
- Truncated to 32 hex characters
- Stored in policy_payload and returned in import response
- Deterministic: same artifact always produces same hash

## Candidate Isolation Behavior

Imported candidates use existing `get_candidate_isolation()`:
- `promotion_blocked: true`
- `publication_blocked: true`
- `live_recommendation_blocked: true`
- `overview_influence_blocked: true`
- `broker_execution_blocked: true`
- `isolated: true`, `all_blocked: true`

## Audit Event Behavior

Three event types:
- `finrlx_research_artifact_import_requested` — logged when valid import begins
- `finrlx_research_artifact_import_completed` — logged after successful import, includes candidate_id, policy_type, artifact_hash, isolation_checks, component_checks, production_fingerprints_unchanged
- `finrlx_research_artifact_import_rejected` — logged when validation fails, includes source, artifact_hash, validation_errors

All events use resilient `_create_audit_event` (log-and-continue on failure).

## Production Fingerprint Behavior

Captured before and after import:
- `recommendations_current`: snapshot_available=true, unchanged=true
- `publication_status`: snapshot_available=true, unchanged=true
- `overview`: snapshot_available=false with reason
- `unchanged`: true (import only creates RLPolicySnapshot, no production data touched)

## Tests Run

```
398 passed, 2 skipped — zero regressions
```

Phase 8E tests (23):
- 6 validation tests (valid, missing fields, unsafe flags, invalid algorithm)
- 9 import tests (acknowledgement, rejection, creation, safety flags, hash, isolation, fingerprints, audit, candidate list/detail)
- 2 audit persistence tests (completed + rejected events)
- 6 safety regression tests (broker, recommendations, overview, publication, benchmark, existing endpoints)

## Backend Test Results

All 398 tests pass including all Phase 8A/8B/8C/8D/8E tests.

## Frontend Build Status

Not touched. No frontend changes.

## Production Smoke Commands

```powershell
$base = "https://backend-production-aab8.up.railway.app/api/v1"

# Health
Invoke-RestMethod "$base/health"

# FinRL-X status
Invoke-RestMethod "$base/rl/finrlx/status"

# Validate artifact
$artifact = @{
  artifact_type = "finrlx_cpu_rl_research_artifact"
  schema_version = "1.0"
  research_only = $true
  offline_only = $true
  shadow_only = $true
  not_eligible_for_promotion = $true
  live_pipeline_influence = $false
  no_broker_execution = $true
  no_publication_influence = $true
  no_recommendation_pollution = $true
  algorithm = "PPO"
  real_neural_training = $true
  cpu_only = $true
  synthetic_data = $true
  dataset_summary = @{ row_count = 60; synthetic = $true; source = "smoke_test" }
  training_config = @{ algorithm = "PPO"; timesteps = 200; seed = 42 }
  training_metrics = @{ timesteps = 200; algorithm = "PPO"; seed = 42; total_reward = 0.01 }
  artifact_created_at = "2026-04-26T00:00:00Z"
  warnings = @("Synthetic data smoke artifact.")
}

$valBody = @{ artifact = $artifact } | ConvertTo-Json -Depth 20
Invoke-RestMethod "$base/rl/finrlx/validate-research-artifact" -Method POST -ContentType "application/json" -Body $valBody

# Import without acknowledgement → 422
try {
  Invoke-RestMethod "$base/rl/finrlx/import-research-artifact" -Method POST -ContentType "application/json" -Body (@{ artifact = $artifact; source = "smoke" } | ConvertTo-Json -Depth 20)
} catch { $_.Exception.Response.StatusCode.value__ }  # Expected: 422

# Import with acknowledgement
$importBody = @{ artifact = $artifact; import_acknowledgement = $true; source = "production_smoke"; notes = "Phase 8E smoke test" } | ConvertTo-Json -Depth 20
$import = Invoke-RestMethod "$base/rl/finrlx/import-research-artifact" -Method POST -ContentType "application/json" -Body $importBody
$import.data | ConvertTo-Json -Depth 12

# Verify imported candidate isolation
$cid = $import.data.policy_candidate_id
Invoke-RestMethod "$base/rl/finrlx/candidates/$cid/isolation" | ConvertTo-Json -Depth 10

# Safety checks
try { Invoke-RestMethod "$base/rl/execute" -Method POST -ContentType "application/json" -Body "{}" } catch { $_.Exception.Response.StatusCode.value__ }
Invoke-RestMethod "$base/overview"
Invoke-RestMethod "$base/recommendations/current"
Invoke-RestMethod "$base/publication/status"

# Benchmark regression
$b = Invoke-RestMethod "$base/rl/benchmarks/run" -Method POST -ContentType "application/json" -Body '{"start_date":"2026-03-15","end_date":"2026-04-15"}'
$b.data.status
```

## Known Limitations

1. No frontend UI for artifact import (deferred to Phase 8F)
2. No automatic connection from Phase 8D research container to import endpoint
3. Artifact hash excludes `artifact_created_at` only — other volatile fields could exist
4. No duplicate artifact detection (same artifact can be imported multiple times)
5. No RLTrainingRun created for imported artifacts (training was local)
6. Imported candidates cannot yet be benchmarked against baseline agents (Phase 8F)

## Stop/Go Recommendation for Phase 8F

**GO** — with focus areas:

1. **Benchmark integration**: Allow imported research candidates to be included in `POST /api/v1/rl/benchmarks/run` comparisons
2. **Admin UI**: Add artifact import panel to the existing FinRL-X Admin section (paste JSON, validate, import, see results)
3. **Duplicate detection**: Warn if artifact_hash already imported
4. **Dataset export**: Streamline JSON export from backend for Phase 8D local training

## Safety Confirmations

| Check | Status |
|-------|--------|
| No live RL added | CONFIRMED |
| No broker execution | CONFIRMED |
| No auto-trading | CONFIRMED |
| No recommendation pollution | CONFIRMED |
| No overview pollution | CONFIRMED |
| No publication influence | CONFIRMED |
| No production dependency changes | CONFIRMED |
| Imported artifacts research/offline/shadow only | CONFIRMED |
| No torch/gymnasium/stable-baselines3 in production | CONFIRMED |
| No production PPO/A2C training run | CONFIRMED |
| All imported candidates not eligible for promotion | CONFIRMED |

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | validate-research-artifact endpoint exists | PASS |
| 2 | import-research-artifact endpoint exists | PASS |
| 3 | Valid artifact validates successfully | PASS |
| 4 | Invalid artifact returns 422 with errors | PASS |
| 5 | Import requires import_acknowledgement=true | PASS |
| 6 | Valid import creates research-only candidate | PASS |
| 7 | Imported candidate has safety_flags | PASS |
| 8 | Imported candidate has artifact_hash | PASS |
| 9 | Imported candidate not_eligible_for_promotion=true | PASS |
| 10 | Isolation blocks promotion | PASS |
| 11 | Isolation blocks publication | PASS |
| 12 | Isolation blocks live recommendation | PASS |
| 13 | Isolation blocks overview influence | PASS |
| 14 | Isolation blocks broker execution | PASS |
| 15 | Import captures production_fingerprints | PASS |
| 16 | Import creates audit events | PASS |
| 17 | Rejected import creates audit event | PASS |
| 18 | /recommendations/current unaffected | PASS |
| 19 | /overview unaffected | PASS |
| 20 | /publication/status unaffected | PASS |
| 21 | /rl/execute remains unavailable | PASS |
| 22 | Benchmark workflow works | PASS |
| 23 | Benchmark audit trail works | PASS |
| 24 | Phase 8A/8B/8C endpoints work | PASS |
| 25 | No production dependency changes | PASS |
| 26 | No production PPO/A2C training | PASS |
| 27 | Backend tests pass (398 passed) | PASS |
| 28 | Frontend build if touched | N/A |
| 29 | Design handoff reviewed | PASS |
| 30 | Production smoke commands included | PASS |
| 31 | No live RL/broker/rec/overview/pub influence | PASS |
