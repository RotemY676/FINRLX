# Phase 7F: Benchmark Run Controls & Safe Operator Workflow — Report

**Date:** 2026-04-25
**Phase:** 7F — Admin/Ops benchmark run workflow
**Status:** Complete

---

## 1. Executive Summary

Phase 7F adds a safe "Run Offline Benchmark" workflow to the Admin/Ops page. Operators can configure benchmark name, date range, and agent selection, acknowledge safety conditions via checkbox, then run the benchmark through the existing offline-only backend endpoint. Results auto-refresh the history and select the new report in the drill-down UI.

---

## 2. Files Changed

### Frontend (2 modified)
```
frontend/src/services/api.ts        — added RunRLBenchmarkRequest type + runRLBenchmark() function
frontend/src/app/admin/page.tsx     — added Run Offline Benchmark panel with form, validation, safety ack, loading/success/error states
```

### Documentation (1 created)
```
DOCS/handoff/PHASE_7F_BENCHMARK_RUN_CONTROLS_SAFE_OPERATOR_WORKFLOW_REPORT.md
```

No backend changes — existing `POST /api/v1/rl/benchmarks/run` with `agent_keys` field already supports all requirements.

---

## 3. API/Type Changes

```typescript
export interface RunRLBenchmarkRequest {
  name: string;
  environment_key?: string;
  start_date: string;
  end_date: string;
  agent_keys?: string[];
}

export async function runRLBenchmark(payload: RunRLBenchmarkRequest): Promise<ApiResponse<RLBenchmarkReport>>
```

---

## 4. UI Surfaces Changed

### "Run Offline Benchmark" Panel (NEW)

**Header:** Sparkle icon + "Run Offline Benchmark" + "Offline / Shadow only" badge + "No broker execution" badge

**Form fields:**
- Benchmark name (text input, default "Offline Agent Comparison")
- Start date (date input, default "2026-03-15")
- End date (date input, default "2026-04-15")

**Agent selection:**
- Three checkboxes: heuristic_baseline, random_valid, score_weighted_baseline
- All three checked by default
- Zero agents: error "At least one agent is required"
- Fewer than three: warning "Partial benchmark: not all required baseline agents selected"

**Safety acknowledgment:**
- Checkbox in highlighted panel: "I understand this is an offline/shadow benchmark only. It will not create live recommendations, execute trades, influence production decisions, or affect publication workflow."
- Benchmark cannot run until checked

**Run button:**
- Label: "Run offline benchmark" (sparkle icon)
- Disabled when: loading, not acknowledged, empty name, missing dates, invalid date range, zero agents
- Loading state: "Running offline benchmark..." (clock icon)

**Success state:**
- Green panel: "Benchmark {id}... {status} — {N} agents"
- Auto-refreshes benchmark history
- Auto-selects new benchmark in drill-down

**Error state:**
- Red panel with error message
- Form inputs preserved
- Page does not crash

**Validation:**
- Start date > end date: "Start date must be before end date"
- Empty name: button disabled
- Missing dates: button disabled

---

## 5. Run Workflow Behavior

1. Operator fills name, dates, selects agents
2. Operator checks safety acknowledgment
3. Button becomes enabled
4. Click → loading state visible, button disabled
5. POST /api/v1/rl/benchmarks/run with {name, start_date, end_date, agent_keys}
6. On success: green result, history refreshed, new report selected in drill-down
7. On partial: result shows, warnings propagate from API
8. On error: red error panel, inputs preserved

---

## 6. Design Handoff Review

**Design files reviewed:** `HANDOFF.md`, `INDEX.md`, `tokens.css`, `styles.css` (button patterns: .btn, .btn.primary, .action-bar), `Ops.html`, `Design System.html`

**Patterns reused:**
- Card: `rounded-lg border border-line bg-surface p-pad shadow-sm`
- Primary button: `bg-primary text-primary-ink text-[12px] font-medium` with disabled opacity
- Badges: `bg-surface-3 text-ink-3` for safety labels
- Form inputs: `border border-line bg-surface rounded-md text-[12px]` with focus state
- Success panel: `border-pos bg-pos-soft text-pos-soft-ink`
- Error panel: `border-breach bg-breach-soft text-breach-soft-ink`
- Warning text: `text-caution text-[10px]`
- Confirmation panel: `bg-surface-2 border border-line` with checkbox

**No unrelated UI style was introduced.**

---

## 7. Tests Run

**Backend:** 306 passed, 2 skipped — zero regressions (backend untouched)
**Frontend:** Compiled, types checked, 11/11 pages. `/admin` = 10.6 kB.

---

## 8. Production Smoke Commands

```powershell
$base = "https://backend-production-aab8.up.railway.app/api/v1"
$frontend = "https://frontend-production-7e8b1.up.railway.app"

Invoke-RestMethod "$base/health"
Invoke-RestMethod "$base/rl/adapter/status"

$body = @{
  name = "Phase 7F Smoke Benchmark"
  start_date = "2026-03-15"
  end_date = "2026-04-15"
  agent_keys = @("heuristic_baseline", "random_valid", "score_weighted_baseline")
} | ConvertTo-Json

$b = Invoke-RestMethod "$base/rl/benchmarks/run" -Method POST -ContentType "application/json" -Body $body
$b.data.status
$b.data.is_complete_comparison
$b.data.metrics_by_agent.PSObject.Properties.Name
$b.data.forensic_summary_by_agent.PSObject.Properties.Name
$b.data.safety_flags | ConvertTo-Json -Depth 5

try { Invoke-RestMethod "$base/rl/execute" -Method POST -ContentType "application/json" -Body "{}" } catch { $_.Exception.Response.StatusCode.value__ }
Invoke-RestMethod "$base/overview"
Invoke-RestMethod "$base/recommendations/current"
Invoke-RestMethod "$base/publication/status"
Invoke-WebRequest "$frontend/admin" -UseBasicParsing
```

---

## 9. Manual UI Inspection

1. Open `/admin` → scroll to "Run Offline Benchmark"
2. Verify name/start/end date inputs exist
3. Verify three agent checkboxes exist (all checked by default)
4. Verify safety acknowledgment checkbox exists
5. Verify run button is disabled before acknowledgment
6. Check safety checkbox → button becomes enabled
7. Click "Run offline benchmark" → loading state visible
8. After completion → green success panel appears
9. Benchmark history refreshes with new report at top
10. New report is selected in drill-down
11. Equity curves, forensic steps, safety badges all render
12. Verify no buy/sell/trade/execute language

---

## 10. Known Limitations

1. No custom agent key input (limited to three known agents)
2. No policy snapshot comparison trigger from this panel
3. Date inputs default to hardcoded values (not dynamically from data range)
4. No progress indicator beyond loading text (benchmark runs synchronously)
5. Component tests not available — relies on build/typecheck + manual inspection

---

## 11. Safety Confirmations

- **No live RL added** — CONFIRMED
- **No broker execution added** — CONFIRMED
- **No auto-trading added** — CONFIRMED
- **No recommendation pollution** — CONFIRMED
- **No overview pollution** — CONFIRMED
- **No publication influence** — CONFIRMED
- **RL remains offline/shadow only** — CONFIRMED
- **design/handoff-package reviewed** — CONFIRMED

---

## 12. Recommended Next Phase

```
Phase 8: [Future — FINRL-X Neural Training, Extended Data, Advanced Agents]
Do not start without explicit instruction.
```
