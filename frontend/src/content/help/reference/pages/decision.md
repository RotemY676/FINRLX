---
title: Decision
summary: The detail page for a single recommendation — evidence, weights, disagreement, scenarios.
diataxis: reference
area: reference
updated: 2026-05-22
order: 102
---

The Decision page renders one recommendation in full. Every panel here is read-only by default; mutations happen via the action bar.

<Annotated
  src="/help/screenshots/decision.png"
  alt="The Decision page showing the recommendation header, confidence gauges, action bar, and evidence narrative"
  width={1440}
  height={900}
  callouts={[
    { x: 30, y: 11, n: 1, label: "Recommendation header — ID, status (published), and the moderate-overweight summary the engine narrates." },
    { x: 30, y: 22, n: 2, label: "Confidence gauges — model, data, and operational confidence. Each must clear its policy floor for publication." },
    { x: 14, y: 30, n: 3, label: "Action bar — Save as current thesis, Promote to paper, Defer decision. Every action is audit-trailed." },
    { x: 75, y: 30, n: 4, label: "Compare and Replay — Compare opens the engine matrix; Replay opens the forensic-replay view for this recommendation." },
    { x: 18, y: 50, n: 5, label: "Evidence narrative — per-engine contribution to the rationale, with quantitative caveats and shadow / experimental flags." },
  ]}
  caption="The Decision page on the live workspace. Action-bar buttons are the only state-changing controls on the page."
/>

## Sections

### Evidence narrative

A structured summary of *what changed* since the last cycle: new positions, weight shifts, the engine's stated rationale for the largest changes. Treat as a structured summary, not a transcript of the engine's thoughts. See [Governance and audit](/help/concepts/governance-and-audit#what-governance-does-not-do).

### Engine disagreement

If the recommendation was produced by an ensemble or compared against other engines, this panel shows where they agreed and disagreed at the position level. Disagreement is not bad — it usually means the regime is uncertain. See [Agents and engines](/help/concepts/agents-and-engines#the-ensemble).

### Warning banner

If any [risk-overlay](/help/concepts/risk-overlays) constraint fired during this cycle, a warning banner appears at the top of the page with a link to the breach detail.

### Price · &lt;ticker&gt;

Inline price chart for the currently-selected position. Click a different position in the weights panel to switch.

### Portfolio weights

The published weights. Hover any bar for tooltip with exact weight, sector, and the engine's prior weight for delta.

### Positions

Tabular view of every position with weight, value, sector, and last-trade information.

### Risk constraints

The [overlay](/help/concepts/risk-overlays) panel: each active constraint with engine-raw value, projected value, threshold, and whether it is binding.

### Scenario controls

What-if sliders: change the [cash floor](/help/reference/policy-controls#cash_floor) or [exposure caps](/help/reference/policy-controls#exposure_single) and see how the weights would change. These are *previews* — they do not edit the active policy.

## Actions

- **Save as current thesis** — marks this recommendation as your working baseline; comparisons elsewhere show drift from it.
- **Promote to paper** — publishes the weights to your [paper portfolio](/help/reference/pages/paper). See the [guide](/help/guides/promote-to-paper).
- **Defer decision** — parks the recommendation; it will not auto-promote on the next cycle. See the [guide](/help/guides/defer-or-save-a-thesis).
- **Compare** — opens this recommendation in the [Comparison page](/help/reference/pages/comparison) with the engine matrix pre-loaded.
- **Replay** — opens this recommendation in [Replay](/help/reference/pages/replay) for forensic inspection.

## See also

- [Walk through your first recommendation](/help/getting-started/first-recommendation) — the tutorial.
- [Promote to paper](/help/guides/promote-to-paper) — the how-to.
- [The weight-centric pipeline](/help/concepts/weight-centric-pipeline) — the concept behind the contract.
