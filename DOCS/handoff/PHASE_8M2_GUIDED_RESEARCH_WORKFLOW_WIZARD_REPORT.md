# Phase 8M.2 — Guided Research Workflow Wizard Report

**Date:** 2026-04-29
**Accepted checkpoint:** Phase 8LM-fix3 (commit 4aee37e)
**Fix applied:** Complete wizard — metadata warnings/limitations + readiness checklist
**Classification:** PASS

---

## 1. Executive Summary

Phase 8M.2 adds a complete guided research workflow wizard. The wizard orchestrates Export -> Experiment -> Comparison -> Readiness with inline creation, verification, metadata-only result import (with warnings/limitations), and readiness state management with checklist. Expert tabs preserved. No backend changes.

---

## 2. Files Changed

| File | Action |
|------|--------|
| `frontend/src/app/admin/page.tsx` | Modified — complete wizard with all features |
| No backend changes | Confirmed |
| No api.ts changes | Types already supported warnings/limitations |

---

## 3. Design Handoff Review

**Inspected:** HANDOFF.md, shell.jsx, icons.jsx, Decision Workspace.html. Modal uses existing tokens. `<details>` for collapsible panels. **No design files modified.**

---

## 4-5. Wizard Structure

CTA "Start Research Workflow" -> 4-step modal with stepper. Each step: select existing, create new (collapsible), verify, expert tab link. State carries forward through steps.

---

## 6. Step 1 — Research Data

Select/create dataset export. Create: name, dates, format, features/targets/warnings checkboxes, ack. Verify: artifact_exists/warnings.

## 7. Step 2 — Experiment

Select/create experiments. Create: linked to export, name, hypothesis, ack. **Result import: summary, metrics JSON, warnings (newline-separated), limitations (newline-separated), ack.** Verify: health/warnings.

## 8. Step 3 — Comparison

Select/create comparison. Shows experiment count, metric count, warnings. Verify: health/warnings. "Numeric metric sorting only — does not imply production suitability."

## 9. Step 4 — Readiness Review

Select/create readiness. **Create includes checklist: metric_coverage_reviewed, missing_metrics_reviewed, warnings_reviewed, limitations_reviewed, safety_flags_confirmed.** State update with gate guidance: "Backend gates require reviewed warnings, reviewed limitations, confirmed safety flags, and no blocking findings." Verify: findings/warnings.

---

## 10-11. State/API

Local React state, no persistence. All calls to existing APIs with required acknowledgement checkboxes.

## 12-15. Safety/Acknowledgement/Sanitization/Verify

All preserved. Backend is source of truth. No new endpoints.

## 16-17. Responsive/Expert Tabs

Modal w-full max-w-700px. Collapsible details. 5 tabs preserved. "Open in Expert Tab" on every step.

---

## 18. Tests

- Backend targeted: **180 passed** (no changes)
- Full Phase 8 regression: **266 passed**
- Frontend build: **SUCCESS**
- Frontend typecheck: **SUCCESS**
- Frontend lint: **SUCCESS**

## 19. Unsafe Language Grep: No matches

## 20. Known Limitations

1. Wizard state not persisted across reloads
2. Free step navigation
3. No inline comparison metric table (use Expert Tab)
4. JSON parse errors shown inline but not auto-corrected

## 21. Stop/Go: **GO**
