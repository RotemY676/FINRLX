# Phase 7F.2: Unsafe Wording & Subset Result Truthfulness Final Hotfix — Report

**Date:** 2026-04-25
**Status:** Complete

---

## Root Cause

1. **Unsafe wording:** "Not a live signal." appeared in the equity curve description (line 666). The phrase "live signal" violates UI language restrictions.
2. **Subset truthfulness:** The isFullPass check did not verify that the operator selected all three required baseline agents. A subset run with 1-2 agents would show green success even though it's not a full baseline comparison.

## Exact Text Changed

**Removed:** "Not a live signal."
**Replaced with:** "Offline forensic curve only — no production influence."

**Removed:** "execute trades" (already fixed in 7F.1, confirmed still absent)

## Grep Verification

```
Pattern: "live signal|execute trade|trade now|best investment| buy | sell "
Result: 0 occurrences in frontend/src/app/admin/page.tsx
```

## Subset Benchmark Result Behavior

**Before:** `isFullPass` checked only `report.status === "completed" && report.is_complete_comparison && skipped_agents.length === 0`. If operator selected 1 agent and it completed, green success showed.

**After:** `isFullPass` requires ALL of:
- All 3 required agents selected by operator (`REQUIRED.every(a => agents.includes(a))`)
- All 3 required agents executed by backend (`REQUIRED.every(a => report.executed_agents?.includes(a))`)
- `report.status === "completed"`
- `report.is_complete_comparison === true`
- `skipped_agents.length === 0`

Partial reason is computed and shown in caution panel:
- "not all required baseline agents were selected"
- "not all required baseline agents were executed"
- "N agent(s) skipped"
- "status: partial"

## Files Changed (2)

```
frontend/src/app/admin/page.tsx
DOCS/handoff/PHASE_7F2_UNSAFE_WORDING_SUBSET_TRUTHFULNESS_HOTFIX_REPORT.md
```

Backend: not touched.

## Design Handoff Review

**Files reviewed:** `tokens.css`, `styles.css`, `Design System.html`
**Patterns reused:** Existing `bg-pos-soft`/`bg-caution-soft` panels. No new style.

## Build Result

```
Frontend: ✓ Compiled, types checked, 11/11 pages. /admin = 10.8 kB.
```

## Manual Inspection

1. Navigate to `/admin` → equity curve section → verify "Offline forensic curve only — no production influence."
2. Run benchmark with all 3 agents → verify green success panel
3. Run benchmark with 1 agent → verify caution panel: "partial scope — not all required baseline agents were selected"
4. Search page source for "live signal" → expect 0 results
5. Verify existing drill-down, forensic tabs, trend table, safety badges all still work

## Safety Confirmations

- No "live signal" — CONFIRMED (grep: 0 occurrences)
- No "execute trades" — CONFIRMED (grep: 0 occurrences)
- No buy/sell/trade-now/best-investment — CONFIRMED (grep: 0 occurrences)
- No live RL — CONFIRMED
- No broker execution — CONFIRMED
- No recommendation pollution — CONFIRMED
- No overview pollution — CONFIRMED
- No publication influence — CONFIRMED
- RL remains offline/shadow only — CONFIRMED
- design/handoff-package reviewed — CONFIRMED
