---
title: Policy controls
summary: Every policy control by name — what it does, its default, how to change it.
diataxis: reference
area: reference
updated: 2026-05-22
order: 2
---

A **policy control** is a named parameter that constrains recommendations. Every policy is versioned, editable from the [Policies page](/help/reference/pages/policies), and recorded in the audit trail. The controls below ship with the product; the list is exhaustive for the current release.

## CASH_FLOOR

Minimum percentage of the portfolio held in cash.

| | |
|---|---|
| **Default** | 0.05 (5%) |
| **Allowed range** | 0.00 – 0.50 |
| **Unit** | fraction of portfolio value |
| **Edit at** | Policies → Cash floor |

The cash floor is the most-edited control. Raising it forces the engine to be smaller and gives you a buffer in a turbulent regime; lowering it lets the engine run hot. The [turbulence throttle](/help/concepts/regimes-and-turbulence) can push the *effective* cash floor above the configured value when turbulence crosses its threshold.

A cash floor of zero is permitted but not recommended. Even in steady regimes, a small cash buffer absorbs the slippage and timing noise of multi-name rebalances.

## CONFIDENCE_FLOOR

The minimum acceptable confidence in the three operational layers — data, model, operational. Recommendations below the floor are held back rather than published.

| | |
|---|---|
| **Default** | 0.70 across all three layers |
| **Allowed range** | 0.00 – 1.00 per layer |
| **Unit** | scalar confidence (0 = unusable, 1 = fully reliable) |
| **Edit at** | Policies → Confidence floor |

The three layers are:

- **Data confidence.** Is the data fresh enough? Is the universe coverage complete? Is the feature pipeline reporting all expected outputs?
- **Model confidence.** Has the engine completed its training cycle inside the cadence? Does the most recent validation Sharpe exceed the minimum acceptable?
- **Operational confidence.** Is the publication queue healthy? Are there open incidents on the audit trail?

You can edit each layer's floor independently. Lowering data confidence is the most consequential edit: it lets the engine publish on partial feeds, which can mask real problems. Do this only when you understand the operational implication.

## EXPOSURE_SINGLE

Maximum allowable weight in a single name.

| | |
|---|---|
| **Default** | 0.10 (10%) |
| **Allowed range** | 0.01 – 0.50 |
| **Unit** | fraction of portfolio value |
| **Edit at** | Policies → Exposure caps |

The exposure cap is the most commonly *binding* overlay constraint. When you see many recommendations capped at exactly 10%, raising the cap will let the engine express stronger views — but also concentrates more risk. Tighten the cap when you want more diversification; loosen it when you trust the engine's conviction.

## EXPOSURE_SECTOR

Maximum allowable aggregate weight in a single sector.

| | |
|---|---|
| **Default** | 0.40 (40%) |
| **Allowed range** | 0.10 – 1.00 |
| **Unit** | fraction of portfolio value |
| **Edit at** | Policies → Exposure caps |

Sector caps prevent the engine from over-concentrating in one part of the market. The default 40% allows the engine to express moderate sector tilts; in volatile cross-sector regimes you may want to tighten to 25–30%.

## TURBULENCE_THRESHOLD

The level above which the [turbulence index](/help/concepts/regimes-and-turbulence) triggers the throttle.

| | |
|---|---|
| **Default** | 1.5 (interpreted relative to the trailing 252-day window) |
| **Allowed range** | 0.5 – 5.0 |
| **Unit** | Mahalanobis-distance percentile-normalized score |
| **Edit at** | Policies → Turbulence |

Lower thresholds mean the throttle triggers more often (more conservative behavior). Higher thresholds mean the throttle triggers only during extreme events. The default 1.5 corresponds to roughly the 90th percentile of historical conditions for typical equity universes.

## TURNOVER_CAP

Maximum allowable fraction of the portfolio traded per rebalance.

| | |
|---|---|
| **Default** | 0.50 (50%) |
| **Allowed range** | 0.05 – 1.00 |
| **Unit** | fraction of portfolio value |
| **Edit at** | Policies → Turnover |

Turnover caps protect against [reward-hacking](/help/concepts/known-pitfalls#reward-hacking) and against engines that over-rotate in volatile periods. The default 50% allows substantial rebalancing while preventing churn; tighten it if you observe excessive trading frequency.

## How edits flow

A policy edit is committed to the audit trail with your user identity, the timestamp, and an optional reason. The next recommendation cycle (typically the next day for daily-rebalancing strategies) picks up the new values automatically. There is no immediate re-derivation — the current recommendation continues to reflect the policy values in force when it was produced.

To re-derive immediately after a policy edit, use the **Re-run** action on the [Decision page](/help/reference/pages/decision). The new derivation will use the freshly edited values and will replace the current recommendation in the queue.

## See also

- [Risk overlays](/help/concepts/risk-overlays) — how these controls are applied.
- [Policies](/help/reference/pages/policies) — the page where you edit them.
- [Investigate a breach](/help/guides/investigate-a-breach) — what to do when a control fires.
