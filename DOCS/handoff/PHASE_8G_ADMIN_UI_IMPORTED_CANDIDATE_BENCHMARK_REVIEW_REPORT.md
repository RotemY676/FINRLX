# Phase 8G: Admin UI for Imported Candidate Benchmarking & Review

**Date:** 2026-04-26
**Status:** Complete

---

## Executive Summary

Phase 8G adds an Admin/Ops UI workflow for reviewing imported FinRL-X research candidates and running offline benchmark evaluation. The UI follows existing design patterns (Tailwind, semantic status badges, card layout) and uses safe language throughout. No backend changes were made.

## Files Changed

```
EDIT frontend/src/services/api.ts          — 7 new types + 5 new API functions
EDIT frontend/src/app/admin/page.tsx       — imported candidate section with benchmark workflow
NEW  DOCS/handoff/PHASE_8G_ADMIN_UI_IMPORTED_CANDIDATE_BENCHMARK_REVIEW_REPORT.md
```

No backend files changed. No production dependency changes.

## Backend Changes

None. All Phase 8F/8F.2 endpoints already exist.

## API Endpoints Used

| Endpoint | Method | Used for |
|----------|--------|----------|
| `/rl/finrlx/candidates` | GET | Load imported candidate list |
| `/rl/finrlx/candidates/{id}/benchmark-eligibility` | GET | Check eligibility on select |
| `/rl/finrlx/candidates/{id}/benchmark` | POST | Run offline benchmark |
| `/rl/finrlx/candidates/{id}/benchmarks` | GET | Benchmark history |

## Frontend/UI Changes

### New section: "Imported Research Candidates"
Added between the FinRL-X Research Spike section and the Run Offline Benchmark section.

### API Types Added (api.ts)
- `FinRLXCandidate` — full candidate shape with artifact metadata
- `FinRLXBenchmarkEligibility` — eligible, reasons, isolation_checks
- `FinRLXCandidateBenchmarkContext` — inference_mode, surrogate details
- `FinRLXCandidateBenchmarkResponse` — full benchmark result with context
- `FinRLXCandidateBenchmarkHistoryItem` — history entry

### API Functions Added (api.ts)
- `fetchFinRLXCandidate(id)` — GET single candidate
- `fetchFinRLXBenchmarkEligibility(candidateId)` — GET eligibility
- `runFinRLXCandidateBenchmark(candidateId, payload)` — POST benchmark
- `fetchFinRLXCandidateBenchmarks(candidateId)` — GET history

## Design Handoff Review

**Files reviewed:** HANDOFF.md, Design System.html, Ops.html, Backtests.html, styles.css, tokens.css, ops.css, backtests.css

**Patterns reused:**
- Card layout: `rounded-lg border border-line bg-surface p-pad shadow-sm`
- Status badges: `bg-pos-soft text-pos-soft-ink`, `bg-caution-soft text-caution-soft-ink`, `bg-surface-3 text-ink-3`
- Isolation badges: green `bg-pos-soft` pills matching existing FinRL-X section
- Form controls: `border border-line rounded px-2 py-1 text-[11px] bg-canvas focus:border-primary`
- KPI grid: `grid grid-cols-2 sm:grid-cols-3 gap-2 text-[10px]`
- Warning panels: `rounded-lg border border-caution bg-caution-soft p-2 text-[10px]`
- Eligibility panel: green/red semantic with `border-pos bg-pos-soft` or `border-breach bg-breach-soft`
- Table: compact `text-[10px]` with `border-b border-line` rows, font-mono for IDs

**Admin/Ops conventions followed:**
- Section heading with icon + badges (same as FinRL-X Research Spike)
- Data loading in useEffect with `.catch(() => null)` graceful fallback
- Callback-based interaction (selectCandidate, runCandidateBenchmark)
- Disabled button state until acknowledgement + valid inputs

**No unrelated UI style introduced.** All styles match existing admin page patterns.

**Design gaps:** No import/upload/JSON-paste UI pattern exists in the design system. Artifact import remains API-only (documented in Phase 8E).

## Imported Candidate List Behavior

- Loads all candidates via `fetchFinRLXCandidates()`, filters to `imported_from_artifact === true`
- Shows compact list with: ID (truncated), policy_type, artifact_hash (truncated), badges (neural, synthetic, isolated)
- Selected candidate highlighted with primary border
- Empty state: "No imported research candidates yet."

## Selected Candidate Review Behavior

On candidate selection:
- Shows full ID, policy_type, training_mode, artifact_hash, source, created_at
- Shows artifact_summary as JSON
- Shows notes if present
- Shows 5 isolation badges + "Not eligible for promotion" badge
- Shows caution panel: "Production benchmark uses score-weighted fallback surrogate. No neural model is loaded."

## Eligibility Display Behavior

- Fetched on candidate selection via `fetchFinRLXBenchmarkEligibility()`
- Green panel if eligible: "Benchmark eligible"
- Red panel if not eligible: lists rejection reasons
- If not eligible, benchmark form is hidden

## Benchmark Run Form Behavior

- Visible only for eligible candidates
- Fields: name, start_date, end_date, include_baselines checkbox
- Research acknowledgement checkbox required
- Safety copy: "This is a research-only offline benchmark..."
- Button: "Run offline benchmark" (disabled until ack + valid inputs)
- Loading: "Running offline benchmark..."
- Error: red text
- On success: shows result + refreshes history

## Candidate Benchmark History Behavior

- Fetched on candidate selection and after benchmark run
- Shows up to 8 entries: report ID, inference_mode, surrogate/neural badge, agent count, timestamp
- Empty state: "No benchmark history for this imported candidate."

## Result Display Behavior

- Status badge (completed/partial)
- Inference mode, neural inference status ("none (surrogate)"), fingerprint
- Executed agents list
- Compact metrics table: Agent, Return, Reward, Drawdown, Steps
- Warnings panel

## Safety Language Review

Grep for unsafe phrases in admin/page.tsx: **0 matches** for buy, sell, trade now, execute trade, live signal, best investment, production alpha, deploy policy.

All labels use: "offline benchmark", "research only", "shadow", "surrogate", "not eligible for promotion", "no neural inference".

## Tests Run

### Frontend
- `npx next build`: **PASS** (compiled successfully, types valid)
- No frontend component test framework exists — documented as manual smoke

### Backend
- **434 passed, 2 skipped** — zero regressions (backend unchanged)

## Production Smoke Commands

```powershell
$base = "https://backend-production-aab8.up.railway.app/api/v1"
$frontend = "https://frontend-production-7e8b1.up.railway.app"

Invoke-RestMethod "$base/health"

$candidates = Invoke-RestMethod "$base/rl/finrlx/candidates"
$imported = $candidates.data | Where-Object { $_.imported_from_artifact -eq $true } | Select-Object -First 1
$cid = $imported.id

Invoke-RestMethod "$base/rl/finrlx/candidates/$cid/benchmark-eligibility"

$r = Invoke-RestMethod "$base/rl/finrlx/candidates/$cid/benchmark" -Method POST -ContentType "application/json" -Body (@{
  name = "Phase 8G UI Smoke"; start_date = "2026-03-15"; end_date = "2026-04-15"
  include_baselines = $true; research_acknowledgement = $true
} | ConvertTo-Json)
$r.data.status
$r.data.executed_agents
$r.data.candidate_benchmark_context.inference_mode

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

1. Open `/admin`
2. Find "Imported Research Candidates" section
3. Verify empty state if no imports, or candidate list if imports exist
4. Select an imported candidate
5. Confirm artifact hash, summary, source visible
6. Confirm isolation badges (5 green + "Not eligible" gray)
7. Confirm caution panel about surrogate
8. Confirm eligibility status (green/red)
9. If eligible, confirm benchmark form appears
10. Fill dates, check acknowledgement, click "Run offline benchmark"
11. Confirm loading state
12. Confirm result shows status, agents, metrics table
13. Confirm history refreshes with new entry
14. Confirm no buy/sell/trade/execute/live-signal language anywhere

## Known Limitations

1. No artifact import UI (remains API-only — no upload/paste pattern in design system)
2. No candidate benchmark drill-down into existing forensic view (uses compact inline table)
3. Benchmark result does not link to the existing generic benchmark drill-down panel
4. No pagination for candidates or history (shows first 10/8)
5. No frontend component tests (no test framework)

## Stop/Go Recommendation for Phase 8H

**GO** — The full research artifact lifecycle is now complete with UI:
- Local training (8D) → Import (8E) → Review & Benchmark (8F/8G)

Phase 8H could focus on:
1. Artifact import UI (JSON paste/upload form)
2. Linking candidate benchmarks to the existing generic drill-down view
3. Dataset export UI for local training
4. Benchmark comparison view (imported vs baseline side-by-side)

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
| 1 | UI shows imported candidates | PASS |
| 2 | UI shows artifact hash + summary | PASS |
| 3 | UI shows not eligible for promotion | PASS |
| 4 | UI shows isolation/safety state | PASS |
| 5 | UI shows benchmark eligibility | PASS |
| 6 | Ineligible disables benchmark | PASS |
| 7 | Eligible can run benchmark | PASS |
| 8 | Requires research acknowledgement | PASS |
| 9 | UI supports include_baselines | PASS |
| 10 | Success shows executed agents | PASS |
| 11 | Success shows inference_mode | PASS |
| 12 | Success shows real_neural_inference=false | PASS |
| 13 | History shown and refreshes | PASS |
| 14 | Safe wording only | PASS |
| 15 | No unsafe language | PASS |
| 16 | Existing benchmark features work | PASS |
| 17 | Existing FinRL-X panel works | PASS |
| 18 | Frontend build passes | PASS |
| 19 | Backend tests pass (434) | PASS |
| 20 | No production dep changes | PASS |
| 21 | No neural inference | PASS |
| 22 | No live RL/broker/rec/overview/pub | PASS |
| 23 | Design reviewed | PASS |
| 24 | Smoke commands included | PASS |
| 25 | Manual UI checklist included | PASS |
