# Phase 7E.1: Per-Agent Forensic Drill-down Hotfix — Report

**Date:** 2026-04-25
**Status:** Complete

---

## Root Cause

Phase 7E's forensic step summary table always rendered from `selectedBenchmark.forensic_summary` (first-agent-only). Although `forensic_summary_by_agent` was available in the response and the UI mentioned "per-agent detail available for X agents", no agent selector existed — users could not actually view per-agent forensic rows.

## Files Changed (2)

```
frontend/src/app/admin/page.tsx     — added selectedForensicAgent state + agent selector chips + per-agent step table
DOCS/handoff/PHASE_7E1_PER_AGENT_FORENSIC_DRILLDOWN_HOTFIX_REPORT.md
```

Backend: not touched.

## UI Behavior Changed

**Before:** Forensic step table showed first-agent rows only. "Per-agent detail available" was stated but not actionable.

**After:**
- When `forensic_summary_by_agent` exists: agent selector chips appear (same styling as queue filter buttons: `bg-primary text-primary-ink` for selected, `text-ink-3 hover:bg-surface-3` for others)
- Clicking a chip switches the forensic step table to that agent's rows
- Default: first available agent
- Label: "Step-level forensic detail for: {agent} · up to 50 rows per agent · offline forensic only"
- When `forensic_summary_by_agent` is missing: falls back to `forensic_summary` with label "Step-level forensic rows currently available for first agent only"
- Shows up to 50 rows (matching backend cap)

## Design Handoff Review

**Files reviewed:** `tokens.css`, `styles.css`, `Ops.html`, `Design System.html`
**Patterns reused:** Agent selector chips use same button styling as queue filter tabs and audit scope tabs (existing admin patterns). Table structure unchanged.
**No new UI style introduced.**

## Build Results

```
Frontend: ✓ Compiled, types checked, 11/11 pages
/admin = 9.6 kB
Backend: not touched — 306 passed (existing)
```

## Manual Inspection

1. Navigate to `/admin` → scroll to "Offline Benchmark — Forensic Comparison"
2. Find "Forensic Step Summary" section
3. Verify agent selector chips appear (e.g., "heuristic baseline", "random valid", "score weighted baseline")
4. Click each chip → table rows change to show that agent's forensic data
5. Verify label updates to show selected agent name
6. Verify "offline forensic only" language present

## Safety Confirmations

- No live RL added — CONFIRMED
- No broker execution added — CONFIRMED
- No recommendation pollution — CONFIRMED
- No overview pollution — CONFIRMED
- No publication influence — CONFIRMED
- RL remains offline/shadow only — CONFIRMED
- design/handoff-package reviewed — CONFIRMED
