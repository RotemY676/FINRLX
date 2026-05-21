---
title: Troubleshooting
summary: Symptoms, likely causes, and what to do next.
diataxis: how-to
area: troubleshooting
updated: 2026-05-22
---

Symptom-first. Pick the thing you are seeing and follow the diagnostic steps. The likely causes are listed in order of frequency.

## "My recommendation is in DRAFT and won't publish"

**Likely cause 1: A confidence floor is below threshold.** Open the [Decision page](/help/reference/pages/decision). The three confidence gauges (model, data, operational) each show their current value vs. the policy floor. The one below the floor is the blocker.

**What to do:**

- If **data confidence** is low, the upstream feed is stale or incomplete. Open [Ops → Data feeds](/help/reference/pages/ops) and identify the feed.
- If **model confidence** is low, the engine has not retrained inside its cadence. Check Ops → Engines for stale training status.
- If **operational confidence** is low, the queue or audit health is degraded. Open Ops → Open incidents.

**What not to do:** Lowering the confidence floor as the fix. That masks the underlying issue.

## "A breach won't clear"

**Likely cause:** The condition that triggered the breach is still true. Breaches are not silenced by clicking around; they clear when either the policy is relaxed or the recommendation is re-derived without violating the constraint.

**What to do:** Follow [Investigate a breach](/help/guides/investigate-a-breach) end-to-end. The two legitimate paths are relax-the-policy and re-derive.

## "My backtest's Sharpe is unrealistically high"

**Likely cause 1: Cost model is too optimistic.** Re-run with the **Pessimistic** cost model. If Sharpe drops dramatically, the original was underestimating frictions.

**Likely cause 2: Regime cherry-picking.** Your backtest window did not include the regime types you will face live. Check the turbulence shading on the equity curve — if the strong returns are concentrated in calm shading, the backtest is fragile.

**Likely cause 3: Look-ahead bias in a custom feature.** Open the feature spec for the experiment and verify every feature has a correct `available_date`. See [Known pitfalls](/help/concepts/known-pitfalls#data-leakage).

## "Paper portfolio is drifting from the target weights"

**Likely cause 1: Execution issue.** A name has experienced corporate action (split, dividend) that has not yet been reflected. Verify on [Universe](/help/reference/pages/universe) → coverage.

**Likely cause 2: Slippage.** Drift of < 50 bps is normal market noise. Drift over 50 bps on a single name usually indicates the cost model is under-estimating real-world slippage.

**What to do:** Check the [Paper portfolio](/help/reference/pages/paper) → Event log. Recent fills and warnings tell the story.

## "Data freshness shows UNAVAILABLE"

**Likely cause:** The freshness probe failed because the feed never reported a freshness payload (not the same as "feed is healthy and I just haven't checked").

**What to do:**

1. Open [Ops → Data feeds](/help/reference/pages/ops).
2. Find the relevant feed. Its **Last fetch** timestamp tells you when it last reported.
3. If the timestamp is recent but freshness is UNAVAILABLE, the feed integration may be misconfigured. Check the integration credentials.
4. If the timestamp is old, the feed itself has stalled. Investigate at the source.

## "My data quality scored High but the recommendation looks wrong"

**Likely cause:** Data quality is one input among many. A recommendation can be plausible per-feature but unhelpful given the regime, the universe, or the policy.

**What to do:**

1. Open [Replay](/help/reference/pages/replay) for the recommendation.
2. Examine the pipeline-stage snapshots — the engine's raw output vs. the published output.
3. If they differ, the overlay shaped the result. The overlay panel shows which constraint fired.
4. If they match, the engine "owned" the call. Compare against other engines on the [Comparison page](/help/reference/pages/comparison) to see whether they agree.

## "An asset I added is stuck in 'Warming up'"

**Likely cause:** Not enough history has been populated yet. The asset needs to clear the configured lookback window.

**Expected wait:** Daily strategies: 3–6 months. Higher-frequency strategies: shorter. The readiness panel on [Universe](/help/reference/pages/universe) shows the precise progress.

**If the wait seems wrong:** Check coverage on the same asset — if coverage is below 100%, the feature pipeline is missing inputs, which can extend the warm-up.

## "Re-derive doesn't seem to change anything"

**Likely cause:** Re-derive uses the *current* engine version and *current* policy controls. If neither has changed since the recommendation was produced, the result is byte-identical by design — that is the [governance determinism guarantee](/help/concepts/governance-and-audit#the-guarantees).

**What to do:** If you wanted re-derive to use *different* policy values, edit the policy first, then re-derive.

## "The wizard keeps reopening"

**Likely cause:** Your profile is marked incomplete in the backend (your last submit did not persist, or your `has_profile` flag was reset).

**What to do:** Complete the wizard to the final step and submit. If the issue persists across sessions, [send feedback](/feedback) — this points to a backend issue.

## See also

- [FAQ](/help/faq) — common questions, less narrowly diagnostic.
- [Known pitfalls](/help/concepts/known-pitfalls) — the catalogue of failure modes the team defends against.
- [Investigate a breach](/help/guides/investigate-a-breach) — when the symptom is a breach.
