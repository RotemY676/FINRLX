---
title: Glossary
summary: Plain-English definitions for every term used across the product.
diataxis: reference
area: glossary
updated: 2026-05-22
---

This glossary is one page, alphabetical, with an anchor per term. Inline mentions across the help center link here using the `Term` component; click any underlined term elsewhere in /help to jump to its entry.

If a term you need is missing, [send feedback](/feedback). The glossary is versioned alongside the product.

## A

### Action
What the engine outputs at each decision step. In FINRLX, the action is a portfolio-weight vector: a list of target allocations across the universe that sums to one. See [The weight-centric pipeline](/help/concepts/weight-centric-pipeline).

### Agent
A reinforcement-learning model that learns a policy mapping market state to actions. FINRLX ships PPO, A2C, SAC, DDPG, TD3, and the ensemble. See [Agents and engines](/help/concepts/agents-and-engines).

### Audit trail
The immutable, timestamped log of every system event — data updates, recommendations, user actions, policy edits, breaches — that constitutes the governance record. See [Governance and audit](/help/concepts/governance-and-audit).

### Available date
The date on which a feature value would have been knowable to a real trader, distinct from the event date the value describes. Used to prevent look-ahead bias.

## B

### Backtest
Replaying decisions against historical data to estimate strategy performance. Cheap and informative but susceptible to overfitting and survivorship bias. See [Backtest vs. paper vs. live](/help/concepts/backtest-vs-paper-vs-live).

### Backtest overfitting
A model that memorizes the backtest window rather than learning a generalizable policy. The dominant failure mode of ML-driven trading systems. See [Known pitfalls](/help/concepts/known-pitfalls#backtest-overfitting).

### Benchmark
A reference portfolio strategy used to evaluate an engine's performance. Equal weight is the universal default; buy-and-hold and risk parity are common additional baselines.

### Breach
A constraint or floor violation raised by the [risk overlay](/help/concepts/risk-overlays). Breaches are recorded in the audit trail and surface on the [Policies](/help/reference/pages/policies) and [Ops](/help/reference/pages/ops) pages.

### Buy-and-hold
A passive benchmark in which the portfolio is set once and never rebalanced. Often surprisingly hard to beat in low-volatility regimes.

## C

### Calmar ratio
Annualized return divided by maximum drawdown. Penalizes large drawdowns; rewards strategies that grow steadily.

### Cash floor
A policy control specifying the minimum percentage of the portfolio held in cash. Default 5%. See [Policy controls](/help/reference/policy-controls).

### Confidence floor
A policy control specifying the minimum acceptable confidence in the data layer, the model layer, and the operational layer. Recommendations below the floor are held back rather than published.

### Coverage
Whether the data feed for a given asset is complete enough for the engine to use. Surfaced per-asset on the [Universe page](/help/reference/pages/universe).

## D

### Data leakage
Any path by which test-set information influences training. Examples include global normalization statistics, forward-looking features, and feature engineering that uses future labels.

### Diátaxis
The documentation-quadrant framework (Tutorial / How-to / Reference / Explanation) used to tag every page in this help center. Every page declares its quadrant in frontmatter.

### Drawdown
The peak-to-trough decline in portfolio value over a window. *Max drawdown* is the largest such decline observed.

## E

### Engine
The strategy that turns market state into portfolio weights. Engines fall into three families: classical optimizers (equal weight, min-var, risk parity), reinforcement-learning agents, and the ensemble.

### Ensemble
An engine that trains PPO, A2C, and DDPG in parallel and picks the best one each rebalance by rolling out-of-sample Sharpe. Useful for regime adaptivity at the cost of interpretability.

### Episode
One pass through the training environment from initial state to terminal state. Backtests are evaluated over many episodes during training.

### Event date
The date that a feature value describes (e.g., the quarter ending 31 March), distinct from the *available date* when it would have been knowable.

### Exposure cap
A policy control specifying the maximum allowable weight in a single name or sector. Enforced by the [risk overlay](/help/concepts/risk-overlays).

## F

### Feature
A computed value the engine sees about an asset at a time step — price returns, technical indicators, fundamentals. See [Universe and features](/help/concepts/universe-and-features).

## H

### Holding period
The duration a position is expected to be held before rebalance. Longer holdings reduce turnover and cost drag.

## L

### Look-ahead bias
Using information not knowable at the decision time. A specific kind of data leakage. See [Known pitfalls](/help/concepts/known-pitfalls).

### Lookback window
The number of past time steps used to compute features and to give the engine context at each decision.

## M

### Mahalanobis distance
A statistical measure of how unusual a vector is relative to a mean and covariance. The [turbulence index](#turbulence-index) is a Mahalanobis distance on daily returns.

### Max drawdown
The largest peak-to-trough decline in portfolio value over the evaluation window.

## N

### Non-stationarity
The property that the underlying data-generating process changes over time. The reason a single fixed model cannot be trusted to perform across regimes.

## P

### Paper trading
Running the engine with live prices and the same execution model as production, but no real capital at risk. The recommended last gate before live. See [Backtest vs. paper vs. live](/help/concepts/backtest-vs-paper-vs-live).

### Point-in-time data
Data referenced as it would have been known on a given historical date — including universe membership, fundamentals, and any feature with a publication lag.

### Policy
1. In reinforcement learning, the learned mapping from state to action distribution. 2. In FINRLX, a named control that constrains recommendations (e.g., CASH_FLOOR, CONFIDENCE_FLOOR). Context disambiguates.

### Portfolio weights
The sum-to-one vector that specifies target allocation across the universe. The universal contract in FINRLX. See [The weight-centric pipeline](/help/concepts/weight-centric-pipeline).

### Provenance
The chain of evidence — data snapshot, feature spec, engine version, seed, policy controls — that produced a recommendation. Recorded in the audit trail.

## R

### Readiness
Whether the engine has enough history for a given asset to use it. Surfaced per-asset on the [Universe page](/help/reference/pages/universe). Distinct from coverage (which is about feed completeness).

### Rebalance frequency
How often the engine recomputes weights — daily, weekly, monthly. Higher frequency raises turnover and cost drag.

### Regime
A persistent market state with distinct statistical properties. FINRLX classifies into four: risk-on early-cycle, risk-on late-cycle, risk-off high-vol, risk-off recovery. See [Regimes and turbulence](/help/concepts/regimes-and-turbulence).

### Replay
Reconstructing a past recommendation exactly as it was at decision time, using the recorded provenance. The post-trade review tool. See [Governance and audit](/help/concepts/governance-and-audit).

### Reward
The scalar the agent optimizes during training. Usually log-return net of transaction cost. Vulnerable to *reward hacking* if poorly specified.

### Reward hacking
An agent exploits a loophole in the reward function to score high without producing the intended behavior. Example: zero-cost env + turnover-rewarding reward → infinite churn. Defended against by always modeling cost.

### Risk overlay
The layer between an engine's raw weights and the published recommendation that enforces hard constraints, exposure caps, confidence floors, and the turbulence throttle. See [Risk overlays](/help/concepts/risk-overlays).

## S

### Sharpe ratio
Mean excess return divided by standard deviation of returns, annualized. The most-used risk-adjusted performance metric.

### Slippage
The difference between intended and executed price. Underestimating slippage is a top failure mode when moving from backtest to live.

### Sortino ratio
Like Sharpe but penalizes only downside deviation, not all volatility.

### Survivorship bias
Universe selection that silently excludes delisted or removed names, inflating apparent historical returns. Defended against by point-in-time universe membership.

## T

### `total_timesteps`
The training-budget hyperparameter for RL agents. The FinRL FAQ names it the *single most important hyperparameter*; under-trained agents lose to well-trained ones across algorithms.

### Transaction cost
Commission plus spread plus slippage paid per trade. Modeled at backtest configuration; exposed for real at the [Paper portfolio](/help/reference/pages/paper) stage.

### Turbulence index
A Mahalanobis-distance measure of how unusual the current cross-section of returns is relative to the recent window. Crosses its threshold → the [risk overlay](/help/concepts/risk-overlays) throttles new positions. See [Regimes and turbulence](/help/concepts/regimes-and-turbulence).

### Turnover
The fraction of the portfolio traded per period. High turnover amplifies cost drag.

## U

### Universe
The list of tradable assets eligible for inclusion in the portfolio at a given time. Managed with point-in-time membership. See [Universe and features](/help/concepts/universe-and-features).

## W

### Walk-forward
A backtest discipline in which the model is retrained on a rolling window and evaluated on the next out-of-sample slice. The FinRL ensemble uses walk-forward retraining every three months. The defense against overfitting at the model-selection level.

### Weight vector
See [Portfolio weights](#portfolio-weights).
