# Phase 7D.1: RL Benchmark UX Acceptance Hotfix — Report

**Date:** 2026-04-25
**Status:** Complete

---

## Root Cause

Two acceptance gaps in Phase 7D:

1. **Missing safety badge:** `live_pipeline_influence=false` was not displayed. Only 5 of 6 safety dimensions were shown. The badge array omitted the `live_pipeline_influence` key.

2. **Incomplete table highlights:** Agent comparison table only highlighted best return and highest reward. Did not highlight lowest drawdown or lowest turnover, making it harder for operators to compare agent risk/cost profiles.

---

## Files Changed (2)

```
frontend/src/app/admin/page.tsx     — added live_pipeline_influence badge; added lowestDrawdown + lowestTurnover highlights
DOCS/handoff/PHASE_7D1_RL_BENCHMARK_UX_ACCEPTANCE_HOTFIX_REPORT.md
```

Backend: not touched. Existing backend smoke remains valid.

---

## UI Changes

### Safety badges — now 6 of 6
Added `{ key: "live_pipeline_influence", label: "No live pipeline influence", safeWhen: false }`.

The `safeWhen` pattern handles inverted flags: `live_pipeline_influence=false` means safe, so `safeWhen: false` correctly renders the green badge when the value is `false` and the warning badge when `true` or missing.

### Agent table highlights — now 4 metrics

| Metric | Highlight Logic | Safe Language |
|---|---|---|
| Total return | Highest value | Best offline return in this benchmark |
| Total reward | Highest value | Highest offline reward in this benchmark |
| Max drawdown | Closest to zero (least negative) | Lowest drawdown in this benchmark |
| Total turnover | Smallest value | Lowest turnover in this benchmark |

**Drawdown interpretation:** `max_drawdown` is stored as negative (e.g., -0.0163). "Lowest drawdown" = least severe = closest to zero = `Math.max()` of the negative values. So -0.0163 is better than -0.0170.

Updated footnote: "Green highlight: best offline return · highest offline reward · lowest drawdown · lowest turnover in this benchmark. Not a live recommendation."

---

## Design Handoff Review

**Files reviewed:** `tokens.css`, `styles.css`, `Ops.html`, `Engine Comparison.html`, `Design System.html`

**Patterns reused:** Same badge styling (`bg-surface-3 text-ink-3` for safe, `bg-breach-soft text-breach-soft-ink` for warning), same table highlight (`text-pos font-semibold`), same footnote styling (`text-[10px] text-ink-4`).

**No new UI style introduced.**

---

## Tests/Build

```
Frontend build: ✓ Compiled, types checked, 11/11 pages
Backend: not touched — 306 passed (from Phase 7D run)
```

---

## Manual Inspection

Navigate to `/admin` → scroll to "Offline Benchmark — Forensic Comparison":
1. Verify 6 safety badges visible (including "No live pipeline influence")
2. Verify agent table highlights green for: best return, highest reward, lowest drawdown, lowest turnover
3. Verify footnote text
4. Verify no buy/sell/trade/execute language

---

## Safety Confirmations

- No live RL added — CONFIRMED
- No broker execution added — CONFIRMED
- No recommendation pollution — CONFIRMED
- No overview pollution — CONFIRMED
- No publication influence — CONFIRMED
- RL remains offline/shadow only — CONFIRMED
- design/handoff-package reviewed — CONFIRMED
