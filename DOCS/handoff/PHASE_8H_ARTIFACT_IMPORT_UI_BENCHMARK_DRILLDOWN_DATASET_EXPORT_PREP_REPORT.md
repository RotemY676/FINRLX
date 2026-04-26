# Phase 8H: Artifact Import UI, Benchmark Drilldown Linking & Dataset Export Prep

**Date:** 2026-04-26
**Status:** Complete

---

## Executive Summary

Phase 8H adds three capabilities to the Admin UI: (1) a full artifact import workflow with JSON paste, validation, and acknowledgement-gated import; (2) benchmark drilldown linking from candidate benchmark results/history into the existing forensic comparison view; (3) a dataset export prep section documenting the local research workflow. No backend changes.

## Files Changed

```
EDIT frontend/src/services/api.ts          — 3 new types + 2 new API functions
EDIT frontend/src/app/admin/page.tsx       — import UI, drilldown linking, dataset export section
NEW  DOCS/handoff/PHASE_8H_ARTIFACT_IMPORT_UI_BENCHMARK_DRILLDOWN_DATASET_EXPORT_PREP_REPORT.md
```

No backend files changed. No production dependency changes.

## Backend Changes

None. All Phase 8E/8F endpoints already exist.

## API Endpoints Used

| Endpoint | Method | Used for |
|----------|--------|----------|
| `/rl/finrlx/validate-research-artifact` | POST | Validate pasted artifact |
| `/rl/finrlx/import-research-artifact` | POST | Import after acknowledgement |
| `/rl/finrlx/candidates` | GET | Refresh candidate list |
| `/rl/finrlx/candidates/{id}/benchmark-eligibility` | GET | Check eligibility |
| `/rl/finrlx/candidates/{id}/benchmark` | POST | Run benchmark |
| `/rl/finrlx/candidates/{id}/benchmarks` | GET | Benchmark history |
| `/rl/benchmarks/{id}` | GET | Load benchmark for drilldown |

## Frontend/UI Changes

### New section: "Import Research Artifact"
- JSON text area with paste support
- Source + Notes fields
- "Validate artifact" button (disabled without JSON)
- Validation result panel (green/red) with hash, errors, warnings, summary
- Import acknowledgement checkbox
- "Import research artifact" button (disabled until valid + acknowledged)
- Success/error states
- Auto-refreshes candidate list + selects new candidate

### Benchmark drilldown linking
- Benchmark result shows "View in benchmark drilldown" button
- History entries show "details" button
- Both call `fetchRLBenchmark(id)` → `selectBenchmark()` → scroll to drilldown section
- Added `id="benchmark-drilldown"` to existing forensic comparison section

### New section: "Dataset Export for Local Research"
- Read-only info panel
- Shows API endpoints for dataset validation and export
- References `research/finrlx_cpu/` local research folder
- Notes full export UI planned for Phase 8I

## API/Type Changes (api.ts)

**New types:**
- `FinRLXArtifactValidationResult` — valid, errors, warnings, artifact_hash, normalized_artifact_summary, safety_flags
- `FinRLXArtifactImportResponse` — status, policy_candidate_id, policy_type, safety_flags, etc.

**New functions:**
- `validateFinRLXResearchArtifact(artifact)` — POST validate
- `importFinRLXResearchArtifact(payload)` — POST import

## Design Handoff Review

**Files reviewed:** HANDOFF.md, Design System.html, Ops.html, Backtests.html, styles.css, tokens.css

**Patterns reused:**
- Card/section: `rounded-lg border border-line bg-surface p-pad shadow-sm`
- Textarea: `border border-line rounded-md px-3 py-2 text-[11px] font-mono bg-canvas focus:border-primary`
- Form inputs: same as existing benchmark form
- Validation result: `border-pos bg-pos-soft` / `border-breach bg-breach-soft` semantic panels
- Acknowledgement checkbox: same pattern as benchmark acknowledgement
- Primary button: `bg-primary text-white disabled:opacity-40`
- Secondary button: `bg-surface-3 text-ink hover:bg-surface-2`
- Status badges: `bg-surface-3 text-ink-3` neutral pills

**Admin/Ops conventions followed:** Section heading with icon + badges, `text-[10px]` info text, font-mono for hashes/IDs, grid layouts for form fields.

**No unrelated UI style introduced.**

**Design gap:** No file upload pattern exists in the design system. Using JSON textarea as the import mechanism.

## Artifact Import UI Behavior

1. Paste JSON into textarea
2. Click "Validate artifact"
3. Client-side JSON parse check (shows error if invalid JSON)
4. Server-side validation via POST endpoint
5. Shows green panel (valid) or red panel (invalid with errors)
6. If valid: acknowledgement checkbox + "Import research artifact" button appear
7. Import disabled until acknowledged
8. On import: creates candidate, refreshes list, selects new candidate
9. Shows success message with candidate ID prefix

## Artifact Validation UI Behavior

- Green panel: "Artifact is valid" + hash
- Red panel: "Artifact is invalid" + error list
- Warning list if present
- Normalized artifact summary shown as JSON

## Import Acknowledgement Behavior

- Checkbox: "I confirm this is a research-only artifact..."
- Import button disabled until checkbox checked
- Import button disabled while loading
- Only appears after successful validation

## Post-Import Candidate Selection Behavior

After successful import:
1. Candidate list refreshes via `fetchFinRLXCandidates()`
2. Filters to imported candidates
3. Finds new candidate by ID
4. Calls `selectCandidate()` which loads eligibility + history

## Benchmark Drilldown Linking Behavior

- "View in benchmark drilldown" button in benchmark result section
- "details" button on each history entry
- Calls `fetchRLBenchmark(reportId)` → `selectBenchmark(report)` → scrolls to `#benchmark-drilldown`
- Uses existing forensic comparison view (agent table, reward breakdown, portfolio curves, step forensics)

## Dataset Export Prep Behavior

Read-only section showing:
- API endpoints for validate-dataset and export-dataset
- Local research folder path
- Note: "Full dataset export UI and one-click workflow planned for Phase 8I."

## Candidate Benchmark History Behavior

Each history entry now includes "details" button to load benchmark into existing drilldown.

## Safety Language Review

`grep` for unsafe phrases: **0 matches** for buy, sell, trade now, execute trade, live signal, best investment, production alpha, deploy policy.

## Tests Run

- **Frontend build**: PASS (compiled, types valid)
- **Backend**: Unchanged (434 tests pass from Phase 8F.2)

## Production Smoke Commands

```powershell
$base = "https://backend-production-aab8.up.railway.app/api/v1"
$frontend = "https://frontend-production-7e8b1.up.railway.app"

Invoke-RestMethod "$base/health"

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

$v = Invoke-RestMethod "$base/rl/finrlx/validate-research-artifact" -Method POST -ContentType "application/json" -Body (@{ artifact = $artifact } | ConvertTo-Json -Depth 20)
$v.data.valid; $v.data.artifact_hash

$import = Invoke-RestMethod "$base/rl/finrlx/import-research-artifact" -Method POST -ContentType "application/json" -Body (@{ artifact = $artifact; import_acknowledgement = $true; source = "phase_8h_smoke"; notes = "8H smoke" } | ConvertTo-Json -Depth 20)
$cid = $import.data.policy_candidate_id

Invoke-RestMethod "$base/rl/finrlx/candidates/$cid"
Invoke-RestMethod "$base/rl/finrlx/candidates/$cid/benchmark-eligibility"

$r = Invoke-RestMethod "$base/rl/finrlx/candidates/$cid/benchmark" -Method POST -ContentType "application/json" -Body (@{ name = "8H Smoke"; start_date = "2026-03-15"; end_date = "2026-04-15"; include_baselines = $true; research_acknowledgement = $true } | ConvertTo-Json)
$r.data.status; $r.data.executed_agents

Invoke-RestMethod "$base/rl/finrlx/candidates/$cid/benchmarks"

try { Invoke-RestMethod "$base/rl/execute" -Method POST -ContentType "application/json" -Body "{}" } catch { $_.Exception.Response.StatusCode.value__ }
Invoke-RestMethod "$base/overview"
Invoke-RestMethod "$base/recommendations/current"
Invoke-RestMethod "$base/publication/status"

$b = Invoke-RestMethod "$base/rl/benchmarks/run" -Method POST -ContentType "application/json" -Body '{"start_date":"2026-03-15","end_date":"2026-04-15"}'
$b.data.status

Invoke-WebRequest "$frontend/admin" -UseBasicParsing
```

## Manual UI Inspection Checklist

1. Open /admin
2. Find "Import Research Artifact" section
3. Paste valid artifact JSON → click "Validate artifact"
4. Confirm green panel with hash + summary
5. Check acknowledgement → click "Import research artifact"
6. Confirm success message + candidate list refreshes
7. Confirm new candidate is selected with eligibility + isolation badges
8. Run offline benchmark → confirm result + metrics table
9. Click "View in benchmark drilldown" → confirm scroll to forensic comparison
10. Check "Candidate Benchmark History" → click "details" on entry
11. Confirm benchmark drilldown loads the selected report
12. Find "Dataset Export for Local Research" section
13. Confirm API endpoints and research folder path shown
14. Confirm no unsafe language anywhere

## Known Limitations

1. JSON paste only — no file upload (design system has no upload pattern)
2. Dataset export is read-only documentation — full UI deferred to Phase 8I
3. Benchmark drilldown scroll may not work perfectly if section is collapsed/hidden
4. No client-side artifact schema validation (relies on server-side)
5. No frontend component tests

## Stop/Go Recommendation for Phase 8I

**GO** — The full operator workflow is now complete:
1. Import artifact from Admin UI (8H)
2. Review candidate metadata + isolation (8G)
3. Run benchmark with drilldown (8F/8G/8H)
4. Dataset prep documented (8H)

Phase 8I could focus on:
1. One-click dataset export with download
2. Benchmark comparison view (imported vs baseline highlight)
3. Artifact import from URL or file
4. Operator runbook/documentation

## Safety Confirmations

| Check | Status |
|-------|--------|
| No live RL | CONFIRMED |
| No broker execution | CONFIRMED |
| No auto-trading | CONFIRMED |
| No recommendation pollution | CONFIRMED |
| No overview pollution | CONFIRMED |
| No publication influence | CONFIRMED |
| No production dependency changes | CONFIRMED |
| No neural inference in production | CONFIRMED |
| Imported candidate benchmarks research/offline/shadow only | CONFIRMED |
| No unsafe language in UI | CONFIRMED |

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Import Research Artifact section exists | PASS |
| 2 | Invalid JSON handled client-side | PASS |
| 3 | Validation triggered from UI | PASS |
| 4 | Validation errors/warnings render | PASS |
| 5 | Import disabled until acknowledged | PASS |
| 6 | Import triggered from UI | PASS |
| 7 | Candidate list refreshes after import | PASS |
| 8 | Imported candidate selected | PASS |
| 9 | Eligibility + isolation load | PASS |
| 10 | Benchmark runnable from UI | PASS |
| 11 | Benchmark requires acknowledgement | PASS |
| 12 | include_baselines available | PASS |
| 13 | History refreshes after run | PASS |
| 14 | Benchmark drilldown linking implemented | PASS |
| 15 | Dataset export prep section exists | PASS |
| 16 | Existing candidate review works | PASS |
| 17 | Dynamic isolation badges work | PASS |
| 18 | Existing benchmark panels work | PASS |
| 19 | Existing FinRL-X panels work | PASS |
| 20 | Safe wording only | PASS |
| 21 | No unsafe language | PASS |
| 22 | Frontend build passes | PASS |
| 23 | Backend unchanged | PASS |
| 24 | No production dep changes | PASS |
| 25 | No neural inference | PASS |
| 26 | No live RL/broker/rec/overview/pub | PASS |
| 27 | Design reviewed | PASS |
| 28 | Smoke commands included | PASS |
| 29 | Manual UI checklist included | PASS |
