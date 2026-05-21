---
title: Policies
summary: Active breaches, named policy controls, and their effective values.
diataxis: reference
area: reference
updated: 2026-05-22
order: 108
---

The Policies page is where you read and edit [policy controls](/help/reference/policy-controls) — the named parameters that constrain recommendations. It is also where active breaches are listed and resolved.

<Annotated
  src="/help/screenshots/policies.png"
  alt="The Policies page showing the active-breach banner, CASH_FLOOR control, and the three CONFIDENCE_FLOOR layers"
  width={1440}
  height={900}
  callouts={[
    { x: 30, y: 12, n: 1, label: "Active breaches banner — the constraint that fired, with current vs. threshold and the actor who acknowledged." },
    { x: 14, y: 22, n: 2, label: "CASH_FLOOR section — the minimum cash percentage policy. Edit / History buttons on the right open the editor or the audit trail." },
    { x: 14, y: 30, n: 3, label: "CONFIDENCE_FLOOR (data) — minimum acceptable data confidence; recommendations below this are held in DRAFT." },
    { x: 14, y: 42, n: 4, label: "CONFIDENCE_FLOOR (model) — minimum acceptable model confidence; gated by the engine's recent validation Sharpe." },
    { x: 14, y: 56, n: 5, label: "CONFIDENCE_FLOOR (operational) — minimum acceptable operational confidence; gated by queue health and audit integrity." },
  ]}
  caption="Policy editor on the live workspace. Each named control has the same edit / history pattern; the breach banner is the action item."
/>

## Sections

### Active breaches

A list of every breach raised in the recent past that has not been resolved. Each row shows: the constraint that fired, the cycle it fired on, the engine's raw value vs. the threshold, the actor who acknowledged it (if any), and a link to the [Decision page](/help/reference/pages/decision) for that cycle.

Two actions per row:

- **Acknowledge** — record that you have seen the breach; it remains active but is no longer "unread."
- **Resolve** — record that the breach has been addressed (policy relaxed, recommendation re-derived, etc.) with a required reason.

### CASH_FLOOR

Editable slider plus the current value. The right-side panel shows the most recent cycle's effective cash level next to the policy floor, so you can see whether the floor is binding.

### CONFIDENCE_FLOOR

Three editable sliders for data, model, and operational confidence. Each shows the latest measured confidence next to the floor. When measured confidence is below the floor, the next cycle's recommendation will be held in DRAFT.

### Other controls

EXPOSURE_SINGLE, EXPOSURE_SECTOR, TURNOVER_CAP, TURBULENCE_THRESHOLD. Each is presented with the same pattern: current value, slider, recent observed value, edit-reason field.

## Audit trail panel

A reverse-chronological log of policy edits with actor, timestamp, change diff, and reason. Click any entry to see the full state diff.

## Patterns of use

- Tightening for a regime transition — raise CASH_FLOOR and tighten EXPOSURE_SECTOR before promoting recommendations during a regime shift.
- Loosening for a calm window — lower turbulence threshold and exposure caps when conditions are steady and the engine's conviction is high.
- Investigating a breach — open from the Active breaches list, identify the constraint, decide between [relaxing or re-deriving](/help/guides/investigate-a-breach).

## See also

- [Policy controls](/help/reference/policy-controls) — the full catalogue.
- [Edit a policy](/help/guides/edit-a-policy) — the how-to.
- [Investigate a breach](/help/guides/investigate-a-breach) — the how-to.
- [Risk overlays](/help/concepts/risk-overlays) — the concept behind these controls.
