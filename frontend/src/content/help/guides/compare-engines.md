---
title: Compare engines
summary: Use the Comparison page to put two or more engines side-by-side.
diataxis: how-to
area: guides
updated: 2026-05-22
order: 2
---

The [Comparison page](/help/reference/pages/comparison) renders an engine matrix that lets you see, for the same universe and the same window, how each engine would allocate. Use this to gut-check an engine's behavior before promoting.

## Steps

1. **Open Comparison.** Sidebar → WORKSPACES → Engine comparison.
2. **Add an engine** via the toolbar selector. Start with the engine that produced your current recommendation plus equal weight as the baseline.
3. **Read the matrix.** Each column is an engine; each row is a metric. The numbers are computed over the *same* window and the *same* universe — they are comparable.
4. **Read the Engine Alignment scatter.** Each point is a position; the axes are two engines' recommended weights. Points on the diagonal mean both engines agree.
5. **Read the Weight Comparison bars.** Per-name bars showing recommended weights vs. the equal-weight benchmark. Tall positive bars = the engine likes the name; tall negative bars = avoids.

## How to interpret disagreement

Disagreement is informative:

- **Agreement at high conviction.** Multiple engines arrive at the same position from different starting points. This is a strong signal.
- **Disagreement on a single name.** One engine sees something the others don't. Usually a regime-sensitive call. See [Regimes and turbulence](/help/concepts/regimes-and-turbulence).
- **Wholesale disagreement.** The engines have nothing in common. Often a sign that the universe or the feature spec is starving one of them. See [Universe and features](/help/concepts/universe-and-features).

## See also

- [Comparison page](/help/reference/pages/comparison) — the reference.
- [Agents and engines](/help/concepts/agents-and-engines) — the families.
