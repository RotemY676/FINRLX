# Phase 7G.1: Selected Benchmark Audit Linkage & Honest Empty State — Report

**Date:** 2026-04-25
**Status:** Complete

---

## Root Cause

Two UI gaps:
1. `fetchRLBenchmarkAuditForReport(reportId)` was defined in api.ts but never called. Selecting a benchmark did not load its audit events.
2. The governance card was guarded by `selectedBenchmark?.result_fingerprint`, hiding the entire card for older benchmarks without fingerprints. No honest empty state was visible.

## Files Changed (2)

```
frontend/src/app/admin/page.tsx
DOCS/handoff/PHASE_7G1_SELECTED_BENCHMARK_AUDIT_LINKAGE_HOTFIX_REPORT.md
```

Backend: not touched.

## UI Behavior Changed

### Selected benchmark audit linkage
- Added `selectedBenchAudit` state + `selectBenchmark()` helper that calls `fetchRLBenchmarkAuditForReport(b.id)` on every selection
- All `setSelectedBenchmark(...)` calls replaced with `selectBenchmark(...)` — initial load, benchmark run completion, history click
- "Audit Trail — Selected Benchmark" section shows audit events for the selected benchmark with: time, event type, status, agent counts, fingerprint (truncated), invariant status

### Honest empty states
- Governance card now shows for ALL selected benchmarks (guard changed from `result_fingerprint` to `selectedBenchmark`)
- No audit events: "No audit events recorded for this benchmark. Audit trail is available for benchmark runs created after Phase 7G."
- No fingerprint: "No result fingerprint — this benchmark likely predates Phase 7G governance."
- No invariants: "No invariant data — this benchmark likely predates Phase 7G governance."

## Design Handoff Review

**Files reviewed:** `tokens.css`, `styles.css`, `Ops.html`, `Design System.html`
**Patterns reused:** Audit table (same as global audit trail), StatusBadge, invariant badges, card layout.
**No new UI style introduced.**

## Build Results

```
Frontend: ✓ Compiled, types checked, 11/11 pages. /admin = 11.7 kB.
Backend: not touched — 318 passed (existing).
Unsafe language grep: 0 occurrences.
```

## Manual Inspection

1. `/admin` → select a newly created benchmark → "Audit Trail — Selected Benchmark" shows audit events
2. Select an older benchmark (if available) → shows honest empty state for audit/fingerprint/invariants
3. Run a new benchmark → new report auto-selects → audit events appear
4. Global "Benchmark Governance & Audit Trail" table still renders
5. All existing sections (equity curves, forensic tabs, trend table, safety badges) still work

## Safety Confirmations

- No live RL — CONFIRMED
- No broker execution — CONFIRMED
- No recommendation pollution — CONFIRMED
- No overview pollution — CONFIRMED
- No publication influence — CONFIRMED
- No unsafe language — CONFIRMED (grep: 0)
- RL remains offline/shadow only — CONFIRMED
- design/handoff-package reviewed — CONFIRMED
