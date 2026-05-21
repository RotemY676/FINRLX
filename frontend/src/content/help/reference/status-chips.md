---
title: Status chips
summary: The OK / WARN / INFO / UNAVAILABLE pills you see across the workspace — what each means.
diataxis: reference
area: reference
updated: 2026-05-22
order: 1
---

Status chips are small uppercase pills used throughout the workspace to label data freshness, regime state, and operational health. They are the most-clicked element after navigation and the most-misread. This page catalogs every chip, what triggers it, and what action — if any — to take when you see it.

## The four states

Every chip resolves to one of four states:

| State | Color | Meaning |
|---|---|---|
| **OK** | green | The system is in its normal operating range. No action. |
| **INFO** | blue | An informational annotation — context, not an alarm. No action. |
| **WARN** | amber | Something is off-baseline but not blocking. Investigate when convenient. |
| **UNAVAILABLE** | grey | The state could not be computed (feed down, query failed, value missing). Treat as "I don't know," not "all clear." |

The color coding is consistent across the workspace and adapts to dark mode while keeping the same semantic mapping. None of the chips uses red — red is reserved for the **BREACH** label and only appears in the [policy](/help/reference/pages/policies) and [ops](/help/reference/pages/ops) contexts.

## Chip catalogue

The chips below are listed by where they appear and what they report on.

### Data freshness chips

These appear on every panel that depends on a feed.

- **Pipeline data · OK · as of `<timestamp>`** — the upstream feed reported within the SLA window for this panel. Action: none.
- **Pipeline data · WARN · stale** — the upstream feed is older than the warning threshold. Action: open the [Ops page](/help/reference/pages/ops) → Data feeds and confirm the feed is healthy. The panel still renders but should be re-checked before relying on it.
- **Pipeline data · UNAVAILABLE · freshness unavailable** — no recent freshness report from upstream. The most common cause is a brand-new install or a feed that has never reported. Action: same as WARN.

### Regime chips

Appears on the TopBar scope filter and on the Home dashboard.

- **Regime · Risk-on early-cycle / late-cycle / Risk-off high-vol / Risk-off recovery** — the current regime label as classified by the daily indicators. See [Regimes and turbulence](/help/concepts/regimes-and-turbulence).
- **Regime confidence dot** — the small colored dot beside the regime label encodes classifier confidence: green ≥ 0.7, amber 0.4–0.7, red < 0.4. Low confidence usually accompanies a regime transition — the classifier is uncertain because the data is mixed.

### Recommendation chips

Appear on the [Decision page](/help/reference/pages/decision) and the Decision queue.

- **Current recommendation · as of `<timestamp>`** — this is the most-recently published recommendation, and the timestamp is the publication time.
- **Recommendation · DRAFT** — the engine produced weights, but the overlay held them back (a confidence floor fired, or you have not yet promoted). Inspect the overlay panel to find out which.
- **Recommendation · DEFERRED** — you (or a teammate) chose to defer this cycle. The recommendation is parked and will not auto-promote.
- **Recommendation · PROMOTED** — the recommendation is now reflected in the paper portfolio.

### Engine chips

Appear on the [Comparison page](/help/reference/pages/comparison) and the [Ops page](/help/reference/pages/ops) → Engines.

- **Engine · OK · last trained `<timestamp>`** — the engine's last training run completed inside the SLA window.
- **Engine · WARN · stale training** — the engine has not retrained inside the rolling-retraining cadence. Walk-forward retraining is the defense against [regime change](/help/concepts/regimes-and-turbulence); a stale engine is a regime-mismatch risk.
- **Engine · UNAVAILABLE** — the engine has never trained, or training failed. Action: check the training job logs from the [Ops page](/help/reference/pages/ops).

### Operational chips

Appear on the [Ops page](/help/reference/pages/ops).

- **Queue · OK** — the publication queue is consuming entries inside SLA.
- **Queue · WARN** — items are dwelling in the queue beyond the warning threshold.
- **Incident · OPEN** — at least one open incident is recorded. The list shows the count.
- **Audit · OK** — the audit trail has been verified end-to-end since the last check.

### Preview chips

Some panels are intentionally inert pending a future phase. These carry a chip like:

- **Preview only — ships in a later phase** — the panel is a layout placeholder. The data shown is illustrative; interactions are disabled. The most common case today is the Research-assistant tile on the [Home page](/help/reference/pages/home).

## A note on UNAVAILABLE

The single most-misread chip is UNAVAILABLE. It does **not** mean "all clear" or "nothing to report" — it means the system could not compute the state. In practice this usually traces to a missing or delayed feed. Investigate it the same way you would investigate a WARN: open the Ops page → Data feeds and confirm.

If you see UNAVAILABLE persistently on a single panel, that panel is the wrong one to glance at for your decisions. Use a peer panel until the chip clears.

## See also

- [Risk overlays](/help/concepts/risk-overlays) — how confidence floors translate into chip changes.
- [Ops](/help/reference/pages/ops) — the central operational dashboard.
- [Policy controls](/help/reference/policy-controls) — the floors that influence chip thresholds.
