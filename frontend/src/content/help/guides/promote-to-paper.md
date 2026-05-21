---
title: Promote a recommendation to paper
summary: Move a recommendation from "draft" to a paper portfolio that tracks live prices.
diataxis: how-to
area: guides
updated: 2026-05-22
order: 3
---

Promoting to paper sends the current recommendation's weights to your paper portfolio, which then tracks live prices using the same execution model that would be used in production. This is the recommended final gate before any live deployment. See [Backtest vs. paper vs. live](/help/concepts/backtest-vs-paper-vs-live) for why this gate matters.

## Before you start

You need: a recommendation in `published` state (not `draft`, not `deferred`); confidence floors for data, model, and operational layers all above their thresholds (you will see green chips on the [Decision page](/help/reference/pages/decision)); no unresolved breaches on the [Policies page](/help/reference/pages/policies).

## Steps

1. **Open the Decision page** for the recommendation you want to promote. The fastest path is to click the latest recommendation in the home Decision queue.
2. **Read the evidence.** The narrative panel summarizes why the engine wants what it wants. The engine-disagreement panel shows whether other engines agree.
3. **Inspect the warnings.** If there is a warning banner at the top, click into it before promoting — the overlay flagged something.
4. **Click "Promote to paper"** in the action bar. A confirmation modal asks for a one-line reason (optional but recommended for audit).
5. **Confirm.** The recommendation transitions to `promoted`, the paper portfolio rebalances to the new target weights at the next available price, and the event is logged in the audit trail.

## Verify the promotion

After confirming:

- **The Paper portfolio page** now shows the new target weights. Drift should be near zero immediately (within the bid-ask spread).
- **The audit trail entry** appears under [Ops → Audit trail](/help/reference/pages/ops) with your user identity, the timestamp, and the reason if you supplied one.
- **The Decision queue** on the home page surfaces the promoted recommendation with the green `PROMOTED` chip.

## If something looks wrong

Promotion is reversible. To revert:

1. Open [Paper portfolio](/help/reference/pages/paper) → Event log.
2. Find the promotion entry.
3. Click "Revert" — this restores the prior target weights and logs a revert event.

## What to watch after promotion

For the first 30 days, watch:

- **Drift from target.** A drift over 50 bps on any name usually points to an execution issue, not an engine issue.
- **Cumulative return vs. backtest baseline.** A large early gap means the cost model is too optimistic.
- **Operational warnings.** Stale prices and missing fills compound; address them quickly.

## See also

- [Decision page](/help/reference/pages/decision) — where promotion happens.
- [Paper portfolio](/help/reference/pages/paper) — where the result lives.
- [Backtest vs. paper vs. live](/help/concepts/backtest-vs-paper-vs-live) — why paper exists.
