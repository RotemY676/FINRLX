# Phase 8E.1: Imported Candidate Metadata Exposure Hotfix

**Date:** 2026-04-26
**Status:** Complete

---

## Root Cause

`_candidate_dict()` in `finrlx_research.py` did not extract artifact import metadata from `policy_payload`. Fields like `imported_from_artifact`, `artifact_hash`, `artifact_summary`, `source`, and `notes` were stored during import but never exposed in candidate list/detail responses.

## Exact Fields Exposed

Added to `_candidate_dict()` return dict:

| Field | Imported candidate | Non-imported candidate |
|-------|-------------------|----------------------|
| `imported_from_artifact` | `true` | `false` |
| `artifact_hash` | 32-char hex | `null` |
| `artifact_summary` | `{algorithm, real_neural_training, ...}` | `null` |
| `source` | e.g. `"local_research_container"` | `null` |
| `notes` | optional string | `null` |
| `not_eligible_for_promotion` | `true` | `true` |

All fields returned consistently for every FinRL-X candidate (imported or not).

## Candidate Detail Behavior

`GET /api/v1/rl/finrlx/candidates/{id}` now returns full artifact traceability:
```json
{
  "id": "...",
  "policy_type": "finrlx_cpu_ppo_research_import",
  "training_mode": "imported_cpu_ppo_research",
  "real_neural_training": true,
  "imported_from_artifact": true,
  "artifact_hash": "a1b2c3d4...",
  "artifact_summary": { "algorithm": "PPO", "synthetic_data": true, ... },
  "source": "local_research_container",
  "notes": "Phase 8E test import",
  "not_eligible_for_promotion": true,
  "safety_flags": { "research_only": true, ... }
}
```

## Candidate List Behavior

`GET /api/v1/rl/finrlx/candidates` includes all the same fields per candidate. No list/detail split — full metadata in both views.

## Files Changed

```
backend/app/services/finrlx_research.py           — _candidate_dict() expanded
backend/tests/test_phase8e_artifact_import.py      — 3 new metadata tests
DOCS/handoff/PHASE_8E1_IMPORTED_CANDIDATE_METADATA_EXPOSURE_HOTFIX_REPORT.md
```

## Tests Added

- `test_imported_candidate_detail_has_artifact_metadata` — verifies imported_from_artifact, artifact_hash, artifact_summary, source, notes, training_mode, not_eligible_for_promotion
- `test_non_imported_candidate_has_consistent_fields` — verifies non-imported candidates return imported_from_artifact=false, null hash/summary
- `test_candidate_list_includes_artifact_metadata` — verifies list view includes imported_from_artifact and artifact_hash

## Backend Test Results

```
401 passed, 2 skipped — zero regressions
```

## Frontend Status

Not touched.

## Design Handoff Review

No UI changes. Design files reviewed in Phase 8E — no import/upload UI pattern exists. Metadata exposure is API-only.

## Safety Confirmations

| Check | Status |
|-------|--------|
| No live RL | CONFIRMED |
| No broker execution | CONFIRMED |
| No recommendation pollution | CONFIRMED |
| No overview pollution | CONFIRMED |
| No publication influence | CONFIRMED |
| No production dependency changes | CONFIRMED |
| All candidates not_eligible_for_promotion | CONFIRMED |

## Production Smoke Commands

```powershell
$base = "https://backend-production-aab8.up.railway.app/api/v1"

# Import artifact
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

$import = Invoke-RestMethod "$base/rl/finrlx/import-research-artifact" -Method POST -ContentType "application/json" -Body (@{ artifact = $artifact; import_acknowledgement = $true; source = "smoke_8e1" } | ConvertTo-Json -Depth 20)
$cid = $import.data.policy_candidate_id

# Verify candidate detail has metadata
$detail = Invoke-RestMethod "$base/rl/finrlx/candidates/$cid"
$detail.data.imported_from_artifact   # Expected: true
$detail.data.artifact_hash            # Expected: 32-char string
$detail.data.artifact_summary         # Expected: dict with algorithm
$detail.data.not_eligible_for_promotion # Expected: true

# Verify list also has metadata
$list = Invoke-RestMethod "$base/rl/finrlx/candidates"
($list.data | Where-Object { $_.id -eq $cid }).imported_from_artifact  # Expected: true
```

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Import response includes artifact_hash | PASS |
| 2 | Candidate detail: imported_from_artifact=true | PASS |
| 3 | Candidate detail: artifact_hash | PASS |
| 4 | Candidate detail: artifact_summary | PASS |
| 5 | Candidate detail: not_eligible_for_promotion=true | PASS |
| 6 | Candidate list includes imported_from_artifact + artifact_hash | PASS |
| 7 | Isolation blocks all five actions | PASS |
| 8 | Import audit events persist | PASS |
| 9 | production_fingerprints on import | PASS |
| 10 | Invalid import returns 422 | PASS |
| 11 | import_acknowledgement required | PASS |
| 12 | No production dependency changes | PASS |
| 13 | No live RL | PASS |
| 14 | No broker/execution | PASS |
| 15 | No rec/overview/pub influence | PASS |
| 16 | Backend tests pass (401 passed) | PASS |
| 17 | Frontend if touched | N/A |
| 18 | Design reviewed | PASS |
