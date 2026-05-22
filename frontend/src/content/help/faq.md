---
title: Frequently asked questions
summary: Common questions, grouped by intent.
diataxis: how-to
area: faq
updated: 2026-05-22
---

Questions you ask in the first week or so. Grouped by intent. If your question is not answered, [send feedback](/feedback) — the FAQ is updated alongside the product.

## Getting started

### What is FINRLX, exactly?

FINRLX is a decision-intelligence platform for portfolio construction. It is **decision support**, not investment advice. It produces model-driven portfolio weights and the full chain of evidence behind them so you can review, replay, and audit every recommendation. See [What governance does *not* do](/help/concepts/governance-and-audit#what-governance-does-not-do).

### Do I need a finance or ML background to use it?

No. The home page is glanceable. The [welcome wizard](/help/getting-started/understanding-your-profile) sets sensible defaults from your answers. You will get more out of the system if you understand the concepts under [Concepts](/help/concepts/weight-centric-pipeline), but you can use it productively before then.

### Where do I start?

[The five-minute product tour](/help/getting-started/tour). Then [walk through your first recommendation](/help/getting-started/first-recommendation). Then come back to a Concepts page when something in the workspace surprises you.

## Reading recommendations

### Why is my recommendation in DRAFT?

The overlay held it back because at least one [confidence floor](/help/reference/policy-controls#confidence_floor) was below its threshold. Open the [Decision page](/help/reference/pages/decision); the confidence-gauge panel shows which layer (data, model, operational) failed. Resolve the underlying issue (usually a stale feed) and the next cycle will publish.

### Why did the engine pick AAPL over MSFT?

The Evidence narrative panel on the Decision page summarizes the per-engine contribution. For deeper inspection, open Replay → Pipeline-stage snapshots, which expose the engine's raw output (pre-overlay) and the data it saw. See [Replay a decision](/help/guides/replay-a-decision).

### What's the difference between "draft" and "deferred"?

**Draft** means the overlay held the recommendation back automatically (a floor was crossed). **Deferred** means a user explicitly parked it. See [Defer or save a thesis](/help/guides/defer-or-save-a-thesis).

### What is "Engine disagreement"?

A panel on the Decision page that shows how many engines agree at the position level when the ensemble is in use. Disagreement is not bad — it is informative. See [Agents and engines](/help/concepts/agents-and-engines).

## Configuring policies

### How do I raise the cash floor?

[Policies page](/help/reference/pages/policies) → click CASH_FLOOR → Edit → move the slider → enter a one-line reason → Save. The next cycle picks up the new value. See [Edit a policy](/help/guides/edit-a-policy).

### A breach won't clear. What do I do?

Two legitimate resolutions: relax the policy if the engine's response is acceptable for this cycle, or re-derive the recommendation if the breach reveals a real upstream problem. See [Investigate a breach](/help/guides/investigate-a-breach). Do **not** silence the breach.

### Can I roll back a policy edit?

Each policy control's **History** button shows every prior value. Edit to a prior value to roll back — the prior edit remains in the audit trail, and the new "rollback" edit is also audit-logged.

## Backtest and paper

### Why is my backtest's Sharpe so much higher than paper?

The most common cause is an under-modeled cost: your backtest's cost model is too optimistic. Tighten it and re-run. The second most common is regime mismatch — your backtest window did not include conditions like the current live regime. See [Backtest vs. paper vs. live](/help/concepts/backtest-vs-paper-vs-live).

### What's the minimum paper period before going live?

We recommend at least one full rebalance cycle. For daily strategies that's roughly 30 trading days. Watch drift, cumulative return vs. backtest, and operational warnings during that window.

### Can I go straight from backtest to live, skipping paper?

You can, but the platform makes paper the recommended gate for a reason: paper exposes operational realities (feed timing, queue health, engine drift) that no backtest can show. See [Backtest vs. paper vs. live](/help/concepts/backtest-vs-paper-vs-live).

## Universe and data

### Why is an asset I just added still "Warming up"?

It needs to clear the lookback window. For daily strategies, that's typically 3–6 months. The asset is *visible* in the universe but *excluded* from recommendations until it transitions to **Ready**. See [Manage your universe](/help/guides/manage-your-universe).

### How does FINRLX avoid survivorship bias?

Universes are point-in-time. On any historical date, the engine sees the names that were tradable *on that date*, not the names tradable today. Custom universes you build from external sources are flagged "survivorship-unverified" until verified. See [Universe and features](/help/concepts/universe-and-features).

## Troubleshooting

### A data-freshness chip shows UNAVAILABLE. What does that mean?

It means the system could not compute the freshness — not "all clear." Open [Ops → Data feeds](/help/reference/pages/ops); a silent feed is the most likely cause. See [Status chips](/help/reference/status-chips).

### The Research assistant prompts on the home page don't do anything.

The panel on the home dashboard is a placeholder. The actual research assistant ships on the **per-ticker workspace** at [`/research/[ticker]`](/help/reference/pages/research-ticker) — open any ticker to use it. There you'll find:

- **Auto-generated insights** synthesized from the ticker's last 6 SEC quarterly filings (for US-listed names). See [Read cross-quarter insights](/help/guides/read-cross-quarter-insights).
- **Manual document upload + Q&A** — upload a PDF and ask grounded questions about it. See [Upload a document](/help/guides/upload-a-document).

### Where do I report a bug or request a feature?

[Send feedback](/feedback). The form routes to the product team.

## See also

- [Troubleshooting](/help/troubleshooting) — symptom-first diagnostic page.
- [Glossary](/help/glossary) — every term defined.
- [Changelog](/help/changelog) — what changed and when.
