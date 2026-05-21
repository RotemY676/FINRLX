---
title: Risk overlays
summary: Constraints, breaches, floors — the guardrails that sit on top of every recommendation.
diataxis: explanation
area: concepts
updated: 2026-05-22
order: 5
---

A **risk overlay** is the layer between an engine's raw weights and the published recommendation. The overlay's job is to enforce a set of constraints — both hard rules and softer policy floors — so the final weights satisfy the conditions you have committed to. When a constraint cannot be satisfied or a floor is crossed, the overlay raises a **breach**.

## The four overlay families

FINRLX overlays fall into four families. They are applied in order; later overlays cannot violate constraints set by earlier ones.

1. **Hard constraints (always on).** Sum-to-one. No short positions in any name not flagged short-eligible. No name exceeding its exchange-imposed cap. These cannot be relaxed by policy edits.
2. **Exposure caps.** Maximum single-name weight, maximum sector weight. Defaults are conservative; you raise them in the [Policies page](/help/reference/pages/policies) when you have justification.
3. **Confidence floors.** Minimum acceptable confidence in the data layer (have we received fresh enough feeds?), the model layer (is the engine's last-known-good evaluation recent enough?), and the operational layer (is the queue healthy?). Cross a floor and the recommendation is held back rather than published.
4. **Turbulence throttle.** When the [turbulence index](/help/concepts/regimes-and-turbulence) crosses its threshold, the overlay caps new position sizes and forces the cash floor up. This is the "be smaller when the world is loud" rule.

## How a breach surfaces

A breach is not a crash. It is a deliberate, audit-trail-recorded signal that the system did not publish the engine's raw weights as-is. When a breach occurs, three things happen:

- The recommendation is marked with the breach tag in the **Decision** screen, and the relevant overlay panel highlights which constraint fired.
- The breach is added to the **Policy breaches** list on the [Ops](/help/reference/pages/ops) and [Policies](/help/reference/pages/policies) pages.
- The audit trail records the original engine weights, the projected weights after the overlay, and the constraint that fired. This is the data you need to investigate.

The breach does *not* automatically silence the engine. It only changes the published weights. The engine's raw output is still recorded for analysis.

## Two ways breaches get resolved

There are exactly two legitimate ways to clear a breach:

- **Relax the policy** if the breach is real but acceptable. Example: turbulence spiked because of a one-off earnings surprise, the engine's response is reasonable, you want to lift the throttle for this cycle. This is a deliberate, audited action in the [Policies page](/help/reference/pages/policies).
- **Re-derive the recommendation** if the breach reveals a real problem in upstream data or engine state. Example: a confidence floor fired because a data feed was stale. You fix the feed, the next cycle re-derives and the breach clears automatically.

What you do *not* do is silence a breach by deleting it. Breaches are immutable in the audit trail. They can be marked "acknowledged" and "resolved" with a reason, but the record persists.

## Floors vs. caps

A floor sets a *minimum*; a cap sets a *maximum*. The two most consequential floors in FINRLX are:

- **CASH_FLOOR** — the minimum cash percentage in any published recommendation. Default 5%. Raising it forces the engine to be smaller; lowering it lets the engine run hot.
- **CONFIDENCE_FLOOR** — the minimum acceptable confidence across data, model, and operational health. Default 0.7 for each. Lower this only if you understand the operational implications: a recommendation published below the floor is one that the system would normally have held back.

Caps are usually exposure caps (single-name, sector, factor). Defaults are aggressive enough for typical universes; tighten them when you want more spread, loosen when you want more concentration.

## How to read the overlay panel

The overlay panel on the Decision page shows, for each active constraint, three numbers: the engine's raw value, the projected value after the overlay, and the constraint threshold. When the projected value equals the threshold (e.g., a sector at exactly the sector cap), the overlay is binding — relaxing the cap would change the recommendation.

When you see many constraints binding simultaneously, that is a signal: the engine wants to express something the policy disallows. Often the right response is to listen to the engine and revisit the policy, not the other way around — but the choice belongs to you, not the system.

## See also

- [Regimes and turbulence](/help/concepts/regimes-and-turbulence) — the upstream signal that drives the throttle.
- [Investigate a breach](/help/guides/investigate-a-breach) — the recipe.
- [Policy controls](/help/reference/policy-controls) — the named catalogue.
