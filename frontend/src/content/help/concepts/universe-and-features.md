---
title: Universe and features
summary: What goes into a model — assets, indicators, and the discipline of point-in-time data.
diataxis: explanation
area: concepts
updated: 2026-05-22
order: 2
---

Before any engine can produce weights, two questions must be answered: **which assets are eligible** (the *universe*) and **what does the engine see about each asset at each time step** (the *features*). Every downstream choice — model, overlay, backtest realism — is constrained by these two answers. Get them wrong, and the cleanest engine in the world will still produce misleading results.

## The universe

A universe in FINRLX is a list of tradable assets with a *point-in-time* membership history. Point-in-time matters: if today's S&P 500 is your universe, your backtest will silently exclude every name that was in the index in 2018 but has since been delisted, merged, or relegated. That selection bias — known as **survivorship bias** — inflates returns because the names that failed are not in your sample.

To avoid it, FINRLX universes are managed with explicit membership intervals. On any given date, the engine sees the names that were tradable *on that date*, not the names that are tradable *now*. The [Universe page](/help/reference/pages/universe) shows the membership history for every shipped universe.

Three other universe choices matter:

- **Size.** A universe of 1–5 names starves any non-trivial engine. The FinRL FAQ flatly warns that DRL agents perform poorly on single stocks because the state space is too small. Aim for ≥ 20 names for daily trading, more for higher frequencies.
- **Sector spread.** A 50-name universe of one sector behaves like a 5-name universe of independent sectors. Diversity in the universe is a precondition for diversification in the portfolio.
- **Liquidity.** A name with thin volume passes the universe filter but fails at the execution layer (slippage). FINRLX universes exclude assets below a minimum average daily volume by default; the threshold is configurable.

## Features

A feature is anything the engine sees about an asset at a given time step. FINRLX ships with three families:

- **Price features** — returns at multiple horizons, normalized prices, volatility windows.
- **Technical indicators** — MACD, RSI, Bollinger bands, ADX, and so on. These are computed on the price stream and become inputs to the state.
- **Fundamental features** — earnings growth, valuation ratios, balance-sheet metrics. These are *as-of* features: an EPS announced on 30 April is not visible to the engine on 1 April.

Two failure modes dominate feature engineering, and FINRLX defends against both:

### Look-ahead bias

Any feature that uses information from *after* the decision time is a look-ahead. The classic example: rebalancing on 31 March using March-quarter EPS that is only announced in April. Even when the calendar dates line up, the *publication* dates often don't. FINRLX features are stamped with both the *event date* (when the underlying observation occurred) and the *available date* (when a real trader would have known it). Engines see only data with `available_date ≤ decision_time`.

### Normalization leakage

If you normalize your features using statistics computed across the entire training set — and the test set is inside it — your test-set statistics leak into training. FINRLX normalizes features either per-window (using only past data within the lookback) or per-asset using a held-out training prefix. The exact policy is part of the feature spec and is recorded in the audit trail.

## How features enter the engine

Engines do not see raw market data. They see a *state vector* assembled per asset per time step from the chosen feature set. The state vector has fixed shape and a fixed normalization, so the engine can train on it stably. The composition is determined at backtest configuration time and is part of the engine's provenance — replaying a recommendation reconstructs the exact state the engine saw at decision time. See [Governance and audit](/help/concepts/governance-and-audit) for the replay mechanics.

## Practical guidance

- Pick a universe before you pick an engine. Engines are designed for ranges of universe size; picking the engine first locks in a constraint you might not want.
- Validate point-in-time membership before running a backtest. The [Universe page](/help/reference/pages/universe) lists the membership transitions for every shipped universe.
- When adding new features, prefer ones with a *clearly defined available date*. If you cannot answer "when would a real trader have known this?" the feature is not safe to use.
- Keep the feature count modest. More features make the state space larger and harder for any engine to learn; they also raise the surface area for leakage.

## See also

- [The weight-centric pipeline](/help/concepts/weight-centric-pipeline) — what consumes the features.
- [Known pitfalls](/help/concepts/known-pitfalls) — the catalogue of failure modes around data.
- [Universe](/help/reference/pages/universe) — the page you use to manage assets.
