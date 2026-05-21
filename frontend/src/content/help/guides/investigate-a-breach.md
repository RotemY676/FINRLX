---
title: Investigate a breach
summary: A breach has appeared — find the cause, the affected positions, and how to clear it.
diataxis: how-to
area: guides
updated: 2026-05-22
order: 6
---

A breach is raised when a hard constraint cannot be satisfied or when a policy floor is crossed. The [Policies page](/help/reference/pages/policies) lists active breaches; the [Replay page](/help/reference/pages/replay) lets you see the recommendation as it was at the moment the breach was raised.

## Standard triage

1. **Open Policies → Active breaches.** Each row identifies the constraint, the recommendation it fired on, and the engine's raw value vs. the threshold.
2. **Click the breach** to load detail. The page now shows the constraint definition, the contributing positions, and the actor who acknowledged it (if any).
3. **Open Replay for the same recommendation.** Sidebar → Replay & forensics, pick the recommendation by ID or click the Replay link from the breach. This lets you see the full pipeline state at the moment of the breach.
4. **Inspect the overlay panel in Replay.** It shows the engine's raw output, the projected output after the overlay, and the constraint that fired.
5. **Decide between the two legitimate resolutions:**
   - **Relax the policy** if the breach is real but the engine's response is acceptable for this cycle. Edit the relevant control in [Policies](/help/reference/pages/policies); the next cycle will not raise the same breach.
   - **Re-derive the recommendation** if the breach reveals a real problem in upstream data or engine state. Fix the upstream issue (often a stale feed in [Ops → Data feeds](/help/reference/pages/ops)), then click **Re-run** on the [Decision page](/help/reference/pages/decision).
6. **Mark the breach resolved** with a short reason. The breach moves to the resolved list and the audit entry records your action.

## Common breach patterns

### CONFIDENCE_FLOOR (data) crossed

**What it means.** The data layer reported confidence below the floor. Usually because a feed was stale or coverage dropped.

**What to check.** [Ops → Data feeds](/help/reference/pages/ops). If a feed is `UNAVAILABLE`, the breach is real and the fix is in the feed, not the policy.

**Resolution.** Fix the feed, then re-derive. Do **not** lower the data confidence floor as the resolution — that masks the underlying issue.

### EXPOSURE_SINGLE binding

**What it means.** The engine wants more than the cap allows in a single name. The overlay clipped the weight and recorded the gap.

**What to check.** The engine's conviction on that name. The Comparison page shows whether other engines agree.

**Resolution.** If conviction is high and you trust it, **loosen the cap** (e.g., 10% → 12%). If conviction is questionable, **leave the cap** and accept the clipped weight.

### TURBULENCE throttle active

**What it means.** The turbulence index crossed the threshold and the overlay imposed the throttle. This is not a "breach" in the bad sense — it is the system working as designed.

**What to check.** The [turbulence value at decision time](/help/concepts/regimes-and-turbulence) on the Replay page.

**Resolution.** Usually let the throttle ride. Lower the threshold only if you have a specific reason to override and you are willing to publish more risk in a stressed regime.

## What never to do

- **Do not delete a breach.** Breaches are immutable in the audit trail. They can be acknowledged and resolved with a reason; they cannot be erased.
- **Do not silence breaches as a class.** Each one tells you something. Treat them as signals, not noise.

## See also

- [Risk overlays](/help/concepts/risk-overlays) — the concept.
- [Policy controls](/help/reference/policy-controls) — the catalogue.
- [Edit a policy](/help/guides/edit-a-policy) — for the relax-the-policy path.
