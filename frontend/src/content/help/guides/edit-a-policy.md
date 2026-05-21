---
title: Edit a policy
summary: Change a cash floor, confidence floor, or other policy control safely.
diataxis: how-to
area: guides
updated: 2026-05-22
order: 5
---

Policies are the named constraints applied on top of every recommendation. The most-edited controls are [CASH_FLOOR](/help/reference/policy-controls#cash_floor) when the regime turns risk-off and [CONFIDENCE_FLOOR](/help/reference/policy-controls#confidence_floor) when data quality is in question.

## Before you start

You need: the `policy.edit` scope (admin or owner). A clear reason for the edit — it will be recorded in the audit trail.

## Steps

1. **Open Policies.** Sidebar → OPERATIONS → Policies. The full list of named controls renders top-to-bottom.
2. **Find the control you want to change.** Each control is its own card with the current value on the right.
3. **Click "Edit"** on the control's card.
4. **Move the slider** or type the new value in the input.
5. **Enter a reason** in the required field. One short sentence is enough — "tightening for late-cycle regime", "loosening cap on AAPL conviction", etc.
6. **Click "Save".** The new value is committed, the audit trail records the change, and the next recommendation cycle picks up the updated control.

## When the edit takes effect

Policy edits are not retroactive. The currently-published recommendation continues to reflect the values in force when it was produced. The next cycle (typically the next trading day for daily strategies) re-derives using the new values.

To re-derive immediately, open the [Decision page](/help/reference/pages/decision) for the current recommendation and click **Re-run**. The new derivation will use your edited values.

## Patterns of use

- **Tightening for a regime transition.** Raise CASH_FLOOR (e.g., from 5% to 10%) and tighten EXPOSURE_SECTOR (e.g., from 40% to 30%) before promoting recommendations during a regime shift. See [Regimes and turbulence](/help/concepts/regimes-and-turbulence).
- **Loosening for a calm window.** Lower TURBULENCE_THRESHOLD (e.g., from 1.5 to 2.0) when conditions are steady and the engine's conviction is high.
- **Responding to a data issue.** If a data feed is intermittently stale, raise the data CONFIDENCE_FLOOR temporarily so recommendations are held back rather than published on partial data.

## What not to do

- **Do not silence a confidence floor to push out a recommendation.** That defeats the purpose of the floor and breaks the audit story.
- **Do not edit multiple controls in one save.** Each edit should have its own reason and its own audit entry, even if you plan to make several changes in a row.
- **Do not delete an edit by overwriting it.** The history button on each control's card shows every prior value. The audit trail is forever.

## See also

- [Policy controls](/help/reference/policy-controls) — the full catalogue.
- [Policies page](/help/reference/pages/policies) — the editor.
- [Risk overlays](/help/concepts/risk-overlays) — the concept behind the controls.
