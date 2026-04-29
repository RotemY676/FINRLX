# Phase 8M.2 — Guided Research Workflow Wizard Report

**Date:** 2026-04-29
**Accepted checkpoint:** Phase 8LM-fix3 (commit 4aee37e)
**Fix applied:** Complete wizard UX — inline create, import, verify, state update
**Classification:** PASS

---

## 1. Executive Summary

Phase 8M.2 adds a complete guided research workflow wizard to the Admin page. The wizard orchestrates the full research flow (Export -> Experiment -> Comparison -> Readiness Review) with inline creation, verification, metadata-only result import, and readiness state management. The existing 5-tab expert mode is fully preserved. No backend changes were made.

---

## 2. Files Changed

| File | Action |
|------|--------|
| `frontend/src/app/admin/page.tsx` | Modified — complete wizard with all 4 steps |
| No backend changes | Confirmed |
| No api.ts changes | All needed types/functions already existed |

---

## 3. Design Handoff Review

**Inspected:** HANDOFF.md, shell.jsx, icons.jsx, Decision Workspace.html. Modal uses existing surface/line/primary tokens. `<details>` panels for collapsible creation forms. **No design files modified.**

---

## 4. Why Guided Mode Coexists with Expert Tabs

The 5-tab Admin workflow serves expert operators. The wizard adds a guided linear flow. Both coexist — "Open in Expert Tab" links on every step.

---

## 5. Wizard Structure

- CTA: "Start Research Workflow"
- 4-step modal with stepper, Back/Next/Done navigation
- Each step: select existing, create new (collapsible), verify, expert tab link
- State carries forward: exportId -> experimentIds -> comparisonId -> readinessId

---

## 6. Step 1 — Research Data

- Select existing dataset exports from list
- **Create new export:** name, dates, format, features/targets/warnings checkboxes, research acknowledgement. Uses `createFinrlxDatasetExport` API. Shows row count/checksum on success.
- **Verify selected export:** calls `verifyFinrlxDatasetExport`. Shows artifact_exists/warnings.
- "Open in Expert Tab" link

---

## 7. Step 2 — Experiment

- Multi-select existing experiments
- **Create experiment:** linked to selected export. Uses `createFinrlxResearchExperiment` API.
- **Import metadata-only results:** select experiment, result summary, result metrics JSON, acknowledgement. Uses `importFinrlxResearchExperimentResults` API. JSON parse errors shown inline.
- **Verify experiment:** calls `verifyFinrlxResearchExperiment`. Shows health/warnings.
- Guidance: "Need at least 2 experiments for comparison"

---

## 8. Step 3 — Comparison

- Select existing comparisons (shows experiment count, metric count, warnings)
- **Create comparison:** from selected experiments. Uses `createFinrlxExperimentComparison` API.
- **Verify comparison:** calls `verifyFinrlxExperimentComparison`. Shows health/warnings.
- "Numeric metric sorting only — does not imply production suitability"

---

## 9. Step 4 — Readiness Review

- Select existing readiness reviews
- **Create readiness review:** linked to comparison. Uses `createFinrlxResearchReadiness` API. Shows suggested state.
- **Update readiness state:** state selector, reason, acknowledgement. Uses `updateFinrlxResearchReadinessState` API. Backend gates enforced — shows rejection if checklist incomplete.
- **Verify readiness:** calls `verifyFinrlxResearchReadiness`. Shows findings/warnings.
- "Research review ready does not mean production-ready."

---

## 10. State Management

Local React state: wizardOpen, wizardStep, wzExportId, wzExpIds, wzCmpId, wzRdId, wzLoading, wzError, wzSuccess, wzVerifyResult, plus step-local form state for each creation/import/state-update panel.

---

## 11. API Orchestration

All calls go to existing accepted APIs. No new endpoints. No backend changes. Acknowledgement checkboxes required before every API call.

---

## 12. Safety and Isolation

No new backend endpoints. No backend modifications. All acknowledgement gates preserved. Backend sanitizers remain active. No production influence. No /rl/execute.

---

## 13. Acknowledgement Preservation

Every creation/import/state-update action requires an explicit acknowledgement checkbox. The wizard passes `research_acknowledgement: true` or `acknowledgement: true` only when checked.

---

## 14. Sanitization Preservation

Backend remains the source of truth. Wizard shows backend warnings if fields were redacted/dropped.

---

## 15. Read-Only Verification

All verify buttons call existing read-only endpoints. Displayed inline in wizard.

---

## 16. Responsive/Mobile

Modal: `max-w-[700px] w-full`, scrollable `max-h-[90vh]`. Collapsible `<details>` panels. Flex-wrap controls. Touch-friendly checkboxes/buttons.

---

## 17. Expert Tab Preservation

All 5 tabs remain. "Open in Expert Tab" on every wizard step closes wizard and activates relevant tab.

---

## 18. Tests/Checks

- Backend targeted: **180 passed** (no changes)
- Full Phase 8 regression: **266 passed**
- Frontend build: **SUCCESS**
- Frontend typecheck: **SUCCESS**
- Frontend lint: **SUCCESS**

---

## 19. Unsafe Language Grep

No matches.

---

## 20. Known Limitations

1. Wizard state not persisted across reloads
2. Step navigation allows free movement
3. No inline comparison detail view (metric tables) — use Expert Tab
4. No inline readiness checklist editing — use Expert Tab
5. JSON parse errors for metrics shown inline but not auto-corrected

---

## 21. Stop/Go

**GO** — Phase 8M.2 wizard is complete with all requested features.
