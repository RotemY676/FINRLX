# Phase 8M.2 — Guided Research Workflow Wizard Report

**Date:** 2026-04-28
**Accepted checkpoint:** Phase 8LM-fix2 (commit b8ad9ea)
**Classification:** PASS

---

## 1. Executive Summary

Phase 8M.2 adds an optional guided research workflow wizard to the Admin page. The wizard helps operators move through the full research workflow (Export -> Experiment -> Comparison -> Readiness Review) without manually copying IDs between tabs. The existing 5-tab expert mode is fully preserved. The wizard is a UX/orchestration layer only — it calls existing APIs, preserves all acknowledgement gates, and does not bypass backend sanitizers.

---

## 2. Files Changed

| File | Action |
|------|--------|
| `frontend/src/app/admin/page.tsx` | Modified — wizard modal with 4 steps, CTA, state management |
| No backend changes | Backend was not modified |
| No api.ts changes | All needed types/functions already existed |

---

## 3. Design Handoff Review

**Inspected:** HANDOFF.md, shell.jsx, icons.jsx, Decision Workspace.html.

**Relevant conventions:**
- Modal: `fixed inset-0 z-50 flex items-center justify-center` with backdrop blur
- Card: `rounded-xl shadow-xl bg-surface border border-line`
- Button styles: `bg-primary text-primary-ink`, `bg-surface-2 text-ink-3`
- Badge styles: `inline-flex items-center px-1.5 py-0.5 rounded text-[9px]`
- Form inputs: `rounded-md border border-line bg-surface text-[11px]`
- Acknowledgement: checkbox + label pattern

The wizard follows all existing Admin/Ops design language. **No design files were modified.**

---

## 4. Why Guided Mode, Not Replacement

The existing 5-tab Admin workflow serves expert operators who need direct access to any section. The wizard adds a guided path for the common linear workflow without removing expert access. Both modes coexist — the wizard can be closed at any time, and "Open in Expert Tab" links provide seamless transition.

---

## 5. Wizard Structure

- **CTA:** "Start Research Workflow" button above the tab bar
- **Modal:** centered overlay, max-width 700px, scrollable, backdrop blur
- **Stepper:** 4 steps with visual indicators (active=primary, completed=green, pending=surface)
- **Navigation:** Back/Next buttons, dot indicators, Close button
- **Responsive:** full-width on mobile, stacked controls, touch-friendly

---

## 6. Step 1 — Research Data

- Select from existing dataset exports (list view, click to select)
- Selected export highlighted with primary border
- "Open in Expert Tab" link switches to Research Data tab
- Carries `selectedExportId` forward to Step 2

---

## 7. Step 2 — Experiment

- Multi-select from existing experiments (toggle selection)
- Create new experiment linked to `selectedExportId`
- Requires research acknowledgement
- Calls `createFinrlxResearchExperiment` API
- Carries `selectedExperimentIds` forward to Step 3
- Warning shown if fewer than 2 experiments selected

---

## 8. Step 3 — Comparison

- Select existing comparison or create new from selected experiments
- Requires at least 2 experiment IDs
- Requires research acknowledgement
- Calls `createFinrlxExperimentComparison` API
- Shows "numeric metric sorting only — does not imply production suitability"
- Carries `selectedComparisonId` forward to Step 4

---

## 9. Step 4 — Readiness Review

- Select existing readiness review or create new from selected comparison
- Requires research acknowledgement
- Calls `createFinrlxResearchReadiness` API
- Shows suggested readiness state on creation
- Clear text: "Research review ready does not mean production-ready"
- "Open in Expert Tab" for detailed checklist/findings/state management

---

## 10. State Management

Local component state within admin/page.tsx:
- `wizardOpen`, `wizardStep` — modal visibility and step
- `wzExportId`, `wzExpIds`, `wzCmpId`, `wzRdId` — selected/created IDs
- `wzLoading`, `wzError`, `wzSuccess` — action feedback
- Step-local form state for creation forms
- Not persisted across page reloads (intentional for this phase)

---

## 11. API Orchestration

The wizard calls only existing accepted APIs:
- `createFinrlxResearchExperiment`
- `createFinrlxExperimentComparison`
- `createFinrlxResearchReadiness`

All backend acknowledgement gates, sanitizers, and safety flags remain enforced. The wizard passes `research_acknowledgement: true` only when the operator checks the required checkbox.

---

## 12. Safety and Isolation

| Property | Status |
|----------|--------|
| No new backend endpoints | Confirmed |
| No backend modifications | Confirmed |
| Acknowledgement gates preserved | Confirmed |
| Backend sanitizers active | Confirmed |
| No production influence | Confirmed |
| No /rl/execute | Confirmed (404) |
| No unsafe language | Confirmed (grep clean) |

---

## 13-15. Acknowledgement / Sanitization / Read-Only Preservation

All preserved. The wizard is a pure UI orchestration layer that calls existing APIs. Backend is the source of truth for all safety checks.

---

## 16. Responsive/Mobile Considerations

- Modal uses `max-w-[700px]` but `w-full` with padding
- Controls stack with `flex-wrap`
- Scrollable content areas with `max-h` + `overflow-y-auto`
- Long IDs use `font-mono` + `truncate` + `break-all` where needed
- Touch-friendly button/checkbox sizes

---

## 17. Existing Admin Tab Preservation

All 5 tabs remain: Research Data, Experiments, Comparisons, Readiness, Safety/Ops. The wizard opens as a modal overlay — tabs are visible when wizard is closed. "Open in Expert Tab" closes wizard and activates the relevant tab.

---

## 18. Tests/Checks Run

- Backend targeted: **177 passed** (no changes, regression only)
- Full Phase 8 regression: **263 passed**
- Frontend build: **SUCCESS**
- Frontend typecheck: **SUCCESS**
- Frontend lint: **SUCCESS**

---

## 19. Unsafe Language Grep

No matches for: buy, sell, trade now, execute trade, live signal, best investment, production alpha, deploy policy.

---

## 20. Known Limitations

1. Wizard state not persisted across page reloads
2. No inline result import in wizard (available in Expert Tab)
3. No inline verify in wizard (available in Expert Tab)
4. No inline state update in wizard readiness step (available in Expert Tab)
5. Step navigation allows free movement (does not enforce strict linear flow)

---

## 21. Stop/Go

**GO** — Phase 8M.2 is complete. Wizard adds guided UX without breaking expert mode or backend safety.
