---
title: Agents and engines
summary: PPO, A2C, SAC, DDPG, TD3, and the ensemble — in plain English.
diataxis: explanation
area: concepts
updated: 2026-05-22
order: 3
---

An **engine** in FINRLX is a strategy that turns market state into portfolio weights. Engines fall into three families: classical optimizers, reinforcement-learning agents, and the ensemble. The choice of engine is not the most important choice you will make — universe, features, and policy controls usually matter more — but it does shape the kind of behavior the system can express.

## Classical optimizers

The simplest engines do not learn from data; they apply a fixed rule. Three ship with the product:

- **Equal weight.** Every name in the universe gets the same weight. Surprisingly hard to beat in low-volatility steady-growth markets.
- **Minimum variance.** Picks weights to minimize portfolio variance subject to a sum-to-one constraint. Tends to over-concentrate in low-vol names.
- **Risk parity.** Weights inverse to volatility so every name contributes equal risk. A common diversified baseline.

Classical optimizers are useful as **benchmarks**. They are stable, easy to reason about, and they fail in known, well-documented ways. Any RL agent that does not clearly beat equal weight on a robust backtest is not worth deploying.

## Reinforcement-learning agents

FINRLX ships five RL algorithms, all standard from the upstream FinRL family:

| Algorithm | Type | Best for |
|---|---|---|
| **PPO** | On-policy, policy-gradient | Stable training, good first choice |
| **A2C** | On-policy, actor-critic | Fast on multi-core hardware |
| **SAC** | Off-policy, max-entropy | Continuous action spaces, sample-efficient |
| **DDPG** | Off-policy, deterministic | Continuous action, can be unstable |
| **TD3** | Off-policy, twin-critic | DDPG with the worst instabilities fixed |

On-policy agents (PPO, A2C) discard each batch of experience after using it; off-policy agents (SAC, DDPG, TD3) keep a replay buffer and re-use samples. On-policy methods are usually more stable; off-policy methods can be more sample-efficient.

In practice, **PPO is the strongest default** for portfolio-weight tasks. SAC is the second choice if PPO underperforms. DDPG and TD3 are kept for parity with the FinRL benchmark suite but rarely win.

## The ensemble

The ensemble engine trains PPO, A2C, and DDPG in parallel and **picks the best one each rebalance by rolling out-of-sample Sharpe**. The construction is taken from the FinRL ICAIF 2020 ensemble paper, with the same retraining cadence: every three months on a rolling window. Each candidate agent computes weights; the dispatcher picks the agent with the highest validation Sharpe in the most recent window and routes those weights downstream.

The ensemble's appeal is regime adaptivity. PPO often wins in calm markets, A2C in mid-volatility, DDPG when a clear trend is present. By rotating among them, the ensemble tracks the regime instead of locking in to one.

The cost is interpretability. When the ensemble is in PPO mode, you can read the PPO rationale. When it switches to A2C between rebalances, the *reason* for the switch is "A2C had higher validation Sharpe last quarter" — which is true but not narratively satisfying.

## How to think about engine choice

A useful order of operations:

1. Run **equal weight** first as your baseline. If you cannot beat it, the problem is universe / features / policy, not the engine.
2. Run **PPO** as your RL baseline. It is the most-tested and most-stable.
3. Run the **ensemble** if PPO is borderline. The ensemble's regime adaptivity is most useful when no single agent wins consistently.
4. Use the [Comparison page](/help/reference/pages/comparison) to put two engines side-by-side. Agreement at the position level tells you whether they are converging on the same idea or merely hitting the same number from different directions.

## What engines cannot do

A few things to keep in mind:

- **Engines do not learn the market on their own.** They learn a policy that was optimal *for the training window*. If the regime shifts, that policy can become wrong quickly.
- **Hyperparameters matter more than algorithm.** The FinRL FAQ explicitly names `total_timesteps` as the single most important knob. An undertrained SAC will lose to a well-tuned PPO every time.
- **Engines are sensitive to seed.** Re-run any RL training with a different random seed and you will get a different policy. FINRLX records the seed on every recommendation so this is auditable. See [Governance and audit](/help/concepts/governance-and-audit).

## See also

- [The weight-centric pipeline](/help/concepts/weight-centric-pipeline) — the contract every engine produces.
- [Regimes and turbulence](/help/concepts/regimes-and-turbulence) — what shifts under your engine.
- [Known pitfalls](/help/concepts/known-pitfalls) — including reward hacking and overfitting.
