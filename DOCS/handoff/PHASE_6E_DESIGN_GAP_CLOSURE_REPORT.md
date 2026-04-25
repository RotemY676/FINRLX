# Phase 6E: Design Gap Closure & Product Surface Alignment — Report

**Date:** 2026-04-25
**Phase:** 6E — Align product surfaces with design handoff package
**Status:** Complete

---

## 1. Design Files Reviewed

```
design/handoff-package/HANDOFF.md          — Full product spec (668 lines)
design/handoff-package/INDEX.md            — Quick reference (66 lines)
design/handoff-package/tokens.css          — Clean token export (142 lines)
design/handoff-package/styles.css          — Global component library (1248 lines)
design/handoff-package/Overview.html       — Morning triage hub
design/handoff-package/Decision Workspace.html — Recommendation deep dive
design/handoff-package/Engine Comparison.html  — Side-by-side engine votes
design/handoff-package/Ops.html            — Command center
design/handoff-package/Backtests.html      — Model validation
design/handoff-package/Replay.html         — Time-travel forensics
design/handoff-package/Paper Portfolio.html    — Live-but-simulated P&L
design/handoff-package/Policy Editor.html  — Guardrails (not implemented)
design/handoff-package/Integrations.html   — Data source catalog (not implemented)
design/handoff-package/*.jsx               — 52 React component prototypes
design/handoff-package/*.css               — 11 page-specific stylesheets
design/handoff-package/preview-*.png       — 15 preview screenshots
```

---

## 2. Pages Audited

See full audit: `DOCS/handoff/PHASE_6E_DESIGN_GAP_AUDIT.md`

| Page | Before | After | Key Changes |
|---|---|---|---|
| Overview | PARTIAL | PARTIAL+ | Draft rec hint instead of misleading empty state; real health KPIs |
| Decision | PARTIAL | PARTIAL | No changes needed (risk gauges are known limitation) |
| Engine Comparison | PARTIAL | PASS | ML shadow engine labeled with badge |
| Admin/Ops | PASS | PASS | Already aligned in Phase 6D |
| Backtests | PARTIAL | PASS | Typed provenance; provenance section; clean source_type |
| Replay | PARTIAL | PARTIAL+ | Seeded data warning for demo replays |
| Paper Portfolio | PARTIAL | PASS | Source badge; portfolio value; performance summary; test_paper warning |

---

## 3. Frontend Files Changed

### Created (1)
```
frontend/src/components/recommendation/SourceBadge.tsx  — Reusable provenance badge
```

### Modified (7)
```
frontend/src/components/recommendation/StatusBadge.tsx  — Added: approved, deferred, superseded, partial, degraded
frontend/src/services/api.ts                            — Typed provenance fields, added PaperPerformanceSummary
frontend/src/app/page.tsx                               — Draft rec hint, real health KPIs
frontend/src/app/comparison/page.tsx                    — ML shadow engine badge in matrix
frontend/src/app/backtests/page.tsx                     — Typed source_type, provenance section
frontend/src/app/paper/page.tsx                         — Source badge, portfolio value, performance summary
frontend/src/app/replay/page.tsx                        — Seeded data warning
```

---

## 4. Backend Files Changed

None. No backend analytics logic was modified. All changes are frontend-only.

---

## 5. Design Tokens

**Status: Already aligned.** Current `globals.css` and `tailwind.config.ts` accurately map the design package `tokens.css`:
- oklch color system matches (canvas, surface, ink, primary, pos, caution, breach, accent)
- Font families match (Inter Tight, Fraunces, JetBrains Mono)
- Border radius, shadow, density tokens match
- Dark theme supported via `[data-theme="dark"]`
- No token changes were needed.

---

## 6. Badges/Status Labels Standardized

### StatusBadge (recommendation/pipeline status)
Added: `approved`, `deferred`, `superseded`, `partial`, `degraded`
Full list: fresh, published, provisional, published_with_warning, pending, staged, approved, suppressed, deferred, superseded, stale, draft, completed, failed, running, partial, degraded

### SourceBadge (data provenance) — NEW
Supports: `pipeline_backtest`, `pipeline`, `recommendation_paper`, `real`, `seed_demo`, `test_paper`, `unknown`, `shadow`, `experimental`, `needs_more_data`, `eligible_for_review`, `promising_shadow`

---

## 7. Before/After Behavior Summary

### Overview
- **Before:** "No Recommendation Available" with generic hint when no published rec
- **After:** Caution-styled card explaining draft may exist, directing to Decision Workspace. Freshness/Model Health KPIs now from real backend health data instead of hardcoded 94%/96%.

### Engine Comparison
- **Before:** ML engine shown in matrix without any distinction from deterministic engines
- **After:** ML engine row shows "Shadow / experimental" badge, making it clear it doesn't influence live pipeline

### Backtests
- **Before:** `(item as any).source_type` casts; no provenance detail section
- **After:** Properly typed `source_type`, `is_demo`, `lineage_available`, `decision_count` on BacktestListItem and BacktestDetail. Pipeline backtests show a provenance section with decision count, market bar window, and lineage status.

### Paper Portfolio
- **Before:** No source indication, no portfolio value, no performance summary, no test_paper warning
- **After:** Source badge (recommendation_paper/test_paper/seed_demo), portfolio value display, performance summary with return/Sharpe/drawdown/trades, test_paper warning banner, demo data warning.

### Replay
- **Before:** No warning for seeded/demo replay data
- **After:** Caution banner appears when replay warnings contain "seeded" or "demo"

---

## 8. Build Output

```
$ npm run build
✓ Compiled successfully
✓ Linting and checking validity of types
✓ Generating static pages (11/11)

Route (app)                              Size     First Load JS
├ ○ /                                    4.72 kB        94.9 kB
├ ○ /admin                               5.9 kB         96.1 kB
├ ○ /backtests                           2.55 kB         197 kB
├ ○ /comparison                          10.4 kB         198 kB
├ ○ /decision                            13 kB           207 kB
├ ○ /paper                               3.41 kB         194 kB
└ ○ /replay                              3.62 kB        96.5 kB
```

---

## 9. Test Output

No backend changes — backend tests confirmed passing for safety:
```
$ python -m pytest tests/ -v
220 passed, 2 skipped, 1 warning in 17.38s
```

---

## 10. Remaining Design Gaps

1. **Decision risk gauges** — hardcoded (42%, 81%, etc.). Backend doesn't compute per-constraint utilization. Known limitation.
2. **Policy Editor page** — not implemented. Design exists (`Policy Editor.html`). Requires new backend routes.
3. **Universe page** — not implemented. Design exists (`Universe.html`). Requires new backend routes.
4. **Integrations page** — not implemented. Design exists (`Integrations.html`). Requires new backend routes.
5. **Onboarding page** — not implemented. Design exists (`Onboarding.html`). Requires auth/SSO.
6. **States gallery** — not implemented. Design exists (`States.html`). Component state documentation.
7. **Context pane** — implemented for holdings/engines but not for all design surfaces.
8. **App shell** — sidebar nav implemented but design includes scope chip strip, search, notifications bell, avatar — partially present.
9. **Paper valuation curve** — not rendered as chart. Data available via `/paper/{id}/valuations`.
10. **Replay lineage** — feature_set and signal_run IDs available in backend but not displayed in replay detail UI.

---

## 11. Verification Checklist

- [x] Design gap audit created before implementation
- [x] All relevant design/handoff-package files reviewed
- [x] npm run build passes
- [x] Admin/Ops shows ML shadow status clearly (Phase 6D card)
- [x] Backtests distinguish pipeline vs seed/demo
- [x] Paper distinguishes recommendation_paper vs test_paper vs seed_demo
- [x] Overview does not hide pipeline drafts or warnings
- [x] Engine Comparison labels ML as shadow/experimental
- [x] Seeded/demo/unverified data is visibly labeled
- [x] No RL implemented
- [x] No new ML model implemented
- [x] No governance bypass
- [x] No backend analytics refactor
- [x] All 220 backend tests pass

---

## 12. Recommended Next Phase Prompt

```
Phase 7: [Future — Advanced Features]
Options:
  A. Policy Editor + Universe management pages
  B. RL / FINRL-X reinforcement learning integration
  C. Real-time data integration (WebSocket feeds)
  D. RBAC and authentication
  E. iOS app implementation

Do not start any without explicit instruction.
```
