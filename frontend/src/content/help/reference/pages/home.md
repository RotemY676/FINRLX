---
title: Home (Decision Command Center)
summary: Anatomy of the workspace landing page — every panel, every chip.
diataxis: reference
area: reference
updated: 2026-05-22
order: 101
---

The home page is the **Decision Command Center**. It is the only screen designed to be glanced at — every panel is a summary of a deeper screen, and every panel links to it.

<Annotated
  src="/help/screenshots/home.png"
  alt="The Decision Command Center home page with status chips, stat cards, the Decision queue, the Opportunity radar, and the Research assistant"
  width={1440}
  height={900}
  callouts={[
    { x: 88, y: 3, n: 1, label: "Global Help button (?) — opens this Help center from any page in the workspace." },
    { x: 44, y: 4, n: 2, label: "Data freshness chip — UNAVAILABLE here means the upstream feed has not reported. Open Ops → Data feeds to investigate." },
    { x: 70, y: 4, n: 3, label: "Current recommendation chip — green OK with an 'as of' timestamp shows the most recent published cycle." },
    { x: 12, y: 13, n: 4, label: "Regime stat card — the classifier's current label plus its confidence color. See Concepts → Regimes and turbulence." },
    { x: 88, y: 30, n: 5, label: "Research assistant panel — currently labeled 'Preview only — ships in a later phase.' The prompt buttons are inert until the assistant lands." },
  ]}
  caption="The home dashboard as rendered on the live workspace. Numbers map to the legend below."
/>

## Sections

### Decision queue

Shows the latest published recommendation, recommendations in DRAFT state held by the [overlay](/help/concepts/risk-overlays), and any deferred items. Click a row to open the [Decision page](/help/reference/pages/decision) for that recommendation.

### Paper portfolio

Summary card for your paper portfolio: current notional value, recent return, drift from the most recent target weights. Empty state when no recommendation has been promoted. Deep links to [Paper portfolio](/help/reference/pages/paper).

### Opportunity radar

Per-name opportunity scoring derived from the engine's most recent state. Shows the top-N tickers by score, with a delta from the prior cycle. Read this as "what the engine likes right now," not as "what you should buy" — the recommendation page is where that view becomes a portfolio.

### Research events

Recent material events on names in your universe (earnings, corporate actions, etc.). Sourced from the integrations layer. Links to the [News page](/help/reference/pages/news).

### Research assistant

Currently in preview — the prompt buttons are inert and labeled "Preview only — assistant ships in a later phase." When live, this will provide natural-language Q&A over the audit trail and recommendations. For now, the panel exists to reserve the layout slot.

### Governance

A compact summary of audit health: open breaches count, last audit verification, queue depth. Each row links to the relevant detail screen ([Policies](/help/reference/pages/policies), [Ops](/help/reference/pages/ops)).

### Sector tilt

A bar chart of current portfolio sector weights vs. the universe-average sector weights, so you can see where the engine is leaning. Mirrors the more-detailed view on the [Risk page](/help/reference/pages/risk).

## Status chips on this page

Every panel carries a [status chip](/help/reference/status-chips) showing data freshness. UNAVAILABLE on a panel means the underlying feed could not be reached — investigate from [Ops](/help/reference/pages/ops) → Data feeds.

## See also

- [Reading the dashboard](/help/getting-started/reading-the-dashboard) — the tutorial version of this page.
- [Status chips](/help/reference/status-chips) — chip catalogue.
