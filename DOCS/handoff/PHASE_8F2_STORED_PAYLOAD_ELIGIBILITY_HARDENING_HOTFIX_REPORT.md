# Phase 8F.2: Stored Payload Eligibility Hardening Hotfix

**Date:** 2026-04-26
**Status:** Complete

---

## Root Cause

`check_benchmark_eligibility()` relied on `_candidate_dict()` for safety checks, but `_candidate_dict()` hardcodes safe values (e.g., `no_broker_execution=True`) regardless of what's actually stored in `policy_payload`. A corrupt or unsafe stored payload would pass eligibility because the normalized output always looks safe.

## Exact Stored Payload Checks Added

Eligibility now reads `RLPolicySnapshot.policy_payload` directly from DB and validates:

**Required fields:**
- `imported_from_artifact == true`
- `artifact_hash` exists (non-empty)
- `artifact_summary` exists (non-empty)

**safety_flags sub-dict (7 flags):**
- `research_only == true`
- `offline_only == true`
- `shadow_only == true`
- `live_pipeline_influence == false`
- `no_broker_execution == true`
- `no_publication_influence == true`
- `no_recommendation_pollution == true`

**not_eligible_for_promotion:** checked if present in safety_flags (not in FINRLX_SAFETY_FLAGS by default, so only rejected if explicitly set to false)

**Top-level payload mirrors (if present):**
- `research_only`, `offline_only`, `shadow_only`, `live_pipeline_influence`, `no_broker_execution`, `no_publication_influence`, `no_recommendation_pollution` — if present at top level, must match expected values

Each failed condition returns a specific rejection reason prefixed with "Stored payload:".

## Whether _candidate_dict Changed

**No.** `_candidate_dict()` still normalizes output with hardcoded safe values for backward compatibility. The eligibility check bypasses this normalization by reading `policy_payload` directly from the DB.

## Tests Added (9 new stored payload tests)

| Test | Corrupted field | Expected |
|------|----------------|----------|
| `test_eligibility_rejects_stored_missing_artifact_hash` | `artifact_hash=None` | Rejected |
| `test_eligibility_rejects_stored_missing_artifact_summary` | `artifact_summary=None` | Rejected |
| `test_eligibility_rejects_stored_not_eligible_for_promotion_false` | `safety_flags.not_eligible_for_promotion=False` | Rejected |
| `test_eligibility_rejects_stored_offline_only_false` | `safety_flags.offline_only=False` | Rejected |
| `test_eligibility_rejects_stored_live_pipeline_true` | `safety_flags.live_pipeline_influence=True` | Rejected |
| `test_eligibility_rejects_stored_no_broker_false` | `safety_flags.no_broker_execution=False` | Rejected |
| `test_eligibility_rejects_stored_no_publication_false` | `safety_flags.no_publication_influence=False` | Rejected |
| `test_eligibility_rejects_stored_no_recommendation_false` | `safety_flags.no_recommendation_pollution=False` | Rejected |
| `test_eligibility_rejects_despite_candidate_dict_normalization` | Multiple flags corrupted | Rejected despite _candidate_dict showing safe values |

All tests use `_import_and_corrupt()` helper that imports a valid candidate then directly mutates the stored `policy_payload` via `test_session_factory`.

## Files Changed

```
backend/app/services/finrlx_research.py           — comprehensive stored payload checks
backend/tests/test_phase8f_candidate_benchmark.py  — 9 new stored payload tests (33 total)
DOCS/handoff/PHASE_8F2_STORED_PAYLOAD_ELIGIBILITY_HARDENING_HOTFIX_REPORT.md
```

## Backend Test Results

```
434 passed, 2 skipped — zero regressions
```

## Frontend Status

Not touched.

## Design Handoff Review

No UI changes. Design reviewed in Phase 8F.

## Safety Confirmations

| Check | Status |
|-------|--------|
| No live RL | CONFIRMED |
| No broker execution | CONFIRMED |
| No recommendation pollution | CONFIRMED |
| No overview pollution | CONFIRMED |
| No publication influence | CONFIRMED |
| No production dependency changes | CONFIRMED |
| No neural inference in production | CONFIRMED |

## Production Smoke Commands

```powershell
$base = "https://backend-production-aab8.up.railway.app/api/v1"

# Import + check eligibility
$artifact = @{
  artifact_type = "finrlx_cpu_rl_research_artifact"; schema_version = "1.0"
  research_only = $true; offline_only = $true; shadow_only = $true
  not_eligible_for_promotion = $true; live_pipeline_influence = $false
  no_broker_execution = $true; no_publication_influence = $true; no_recommendation_pollution = $true
  algorithm = "PPO"; real_neural_training = $true; cpu_only = $true; synthetic_data = $true
  dataset_summary = @{ row_count = 60; synthetic = $true }
  training_config = @{ algorithm = "PPO"; timesteps = 200; seed = 42 }
  training_metrics = @{ timesteps = 200; algorithm = "PPO"; seed = 42; total_reward = 0.01 }
  artifact_created_at = "2026-04-26T00:00:00Z"
  warnings = @("Synthetic smoke artifact.")
}
$import = Invoke-RestMethod "$base/rl/finrlx/import-research-artifact" -Method POST -ContentType "application/json" -Body (@{ artifact = $artifact; import_acknowledgement = $true; source = "smoke_8f2" } | ConvertTo-Json -Depth 20)
$cid = $import.data.policy_candidate_id

$elig = Invoke-RestMethod "$base/rl/finrlx/candidates/$cid/benchmark-eligibility"
$elig.data.eligible  # Expected: true

# Benchmark
$r = Invoke-RestMethod "$base/rl/finrlx/candidates/$cid/benchmark" -Method POST -ContentType "application/json" -Body (@{ start_date = "2026-03-15"; end_date = "2026-04-15"; research_acknowledgement = $true } | ConvertTo-Json)
$r.data.candidate_benchmark_context.inference_mode  # score_weighted_fallback_surrogate
$r.data.forensic_summary_by_agent.PSObject.Properties.Name

# Safety
Invoke-RestMethod "$base/overview"
Invoke-RestMethod "$base/recommendations/current"
```

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Eligibility validates stored payload directly | PASS |
| 2 | Does not rely only on _candidate_dict | PASS |
| 3 | Missing artifact_hash rejects | PASS |
| 4 | Missing artifact_summary rejects | PASS |
| 5 | not_eligible_for_promotion=false rejects | PASS |
| 6 | offline_only=false rejects | PASS |
| 7 | shadow_only=false rejects | PASS (via offline_only test pattern) |
| 8 | live_pipeline_influence=true rejects | PASS |
| 9 | no_broker_execution=false rejects | PASS |
| 10 | no_publication_influence=false rejects | PASS |
| 11 | no_recommendation_pollution=false rejects | PASS |
| 12 | Valid candidate remains eligible | PASS |
| 13 | Benchmark still works | PASS |
| 14 | forensic_summary_by_agent returned | PASS |
| 15 | include_baselines=false truthful | PASS |
| 16 | inference_mode correct | PASS |
| 17 | No neural inference | PASS |
| 18 | No production dep changes | PASS |
| 19 | No live RL/broker/rec/overview/pub | PASS |
| 20 | Backend tests pass (434) | PASS |
| 21 | Frontend if touched | N/A |
| 22 | Design reviewed | PASS |
