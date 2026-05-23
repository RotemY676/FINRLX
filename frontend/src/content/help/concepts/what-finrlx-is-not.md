---
title: What FINRLX is not
summary: Common assumptions FINRLX deliberately doesn't meet — and where to look instead.
diataxis: explanation
area: concepts
updated: 2026-05-23
order: 9
---

FINRLX is a **decision-intelligence platform for medium-term investing** — opinionated about governance, auditability, and the workflow around the recommendation. The point of this page is to be explicit about what it is *not*, so you don't waste a Saturday discovering a missing feature.

If you came expecting one of the things below, the table at the bottom points you to a project that *does* do it.

## Not a broker

FINRLX does not place orders. The paper portfolio is fully simulated — it computes drift, weights, and P/L as if you had executed at the prevailing close, but no order ever leaves the system. There is no live-trading mode in any release planned for 2026.

If you want to actually trade, you take the published recommendation and execute it yourself, through whatever broker you already use. Provenance metadata on every recommendation (SHA-256 fingerprint, source feature-set IDs, signal-run IDs) makes it straightforward to reconstruct what you saw, when, before the order leaves your hands.

## Not a reinforcement-learning training framework

The RL surfaces (`Phase 7` benchmark UI, `Phase 8` research lane) are for **comparing and governing** model outputs — not for training new agents. The CPU prototype harness validates inputs, captures audit metadata, and exports datasets in a form a researcher can take elsewhere. It does not iterate on weights, it does not run PPO/SAC training loops, and it deliberately ships no `stable-baselines3` integration.

If you want to train DRL agents end-to-end, use the upstream [AI4Finance-Foundation/FinRL-Trading](https://github.com/AI4Finance-Foundation/FinRL-Trading) project, which is purpose-built for that workflow.

## Not for high-frequency or intraday trading

The bar cadence is daily. The default rebalance frequency is monthly (weekly available). The fee model is a fixed 10 bps per turnover. None of these are tuned for sub-day decisions. Forcing the system into an intraday cadence would invalidate the metric assumptions baked into the backtest engine.

## Not a substitute for licensed financial advice

Every Recommendation surface carries the same `DisclaimerBanner` and (on first visit per session) a blocking modal. Both are deliberate — recommendations are research outputs, not regulated advice. The audit chain is there so you have a clean trail if anyone ever needs to ask "why did the system say X on date Y?", not because the system is itself the source of truth on what *you* should do.

## Where to look instead

| If you want… | Look at… |
|:---|:---|
| Live order execution | Your existing broker; or [Alpaca SDK](https://alpaca.markets/sdks/python/) directly |
| DRL training (PPO/SAC) | [AI4Finance-Foundation/FinRL-Trading](https://github.com/AI4Finance-Foundation/FinRL-Trading) |
| Intraday / HFT | [Backtrader](https://github.com/mementum/backtrader), [Lean (QuantConnect)](https://github.com/QuantConnect/Lean) |
| Equity/portfolio research SDK | [bt](https://github.com/pmorissette/bt), [zipline](https://github.com/quantopian/zipline) |
| Regulated investment advice | A licensed financial advisor in your jurisdiction |

## What FINRLX *is*

In one sentence: a workflow + governance layer around the recommendation, where the recommendation itself is produced by a transparent, auditable, multi-engine pipeline. The [agents and engines](/help/concepts/agents-and-engines) page covers how the recommendation is produced. The [governance and audit](/help/concepts/governance-and-audit) page covers what happens to it after it is produced.
