---
title: Regimes and turbulence
summary: How FINRLX detects market state shifts and de-risks when the world looks different.
diataxis: explanation
area: concepts
updated: 2026-05-22
order: 4
---

Markets are **non-stationary**: the data-generating process changes over time. A model that learned to trade a steady-growth regime will not transfer cleanly to a high-volatility one. FINRLX uses two mechanisms to keep recommendations sensible across this shift: a regime classifier and the turbulence index.

## What "regime" means

A regime is a persistent market state with distinct statistical properties. The product currently distinguishes four:

- **Risk-on, early-cycle** — broad-based participation, narrow drawdowns, momentum works.
- **Risk-on, late-cycle** — narrow leadership, valuations stretched, momentum still works but the dispersion across sectors widens.
- **Risk-off, high-vol** — drawdowns deep, correlations rise, mean-reversion strategies hurt.
- **Risk-off, recovery** — volatility easing, breadth improving, value typically leads.

The regime label is computed daily from a small set of robust indicators (cross-sectional dispersion, realized volatility, breadth, term structure of vol) and is surfaced as a chip in the [TopBar](/help/reference/pages/home) and as the "Regime" scope filter throughout the workspace.

Regime is a *summary* of conditions, not a *forecast* of them. A regime label does not say where the market is going; it says where the market has been for the last N days. That is still useful: it tells you which historical periods are most relevant to the current one for backtest interpretation.

## What the turbulence index measures

The turbulence index is a single number capturing how *unusual* the current cross-section of returns is, relative to the recent history. Technically, it is the Mahalanobis distance between today's return vector and the empirical mean and covariance of the trailing window. Big number → today's returns look unlike anything in recent memory. Small number → ordinary day.

Turbulence has three uses inside FINRLX:

1. **Recommendation throttle.** When turbulence crosses a configured threshold, the [risk overlay](/help/concepts/risk-overlays) caps the size of new positions and forces a higher cash floor. This is the "stop adding risk in panicked markets" rule, taken directly from the FinRL ensemble strategy paper.
2. **Backtest stratification.** When you review a backtest, the equity curve is annotated with turbulence shading so you can see how much of your return came in calm vs. turbulent conditions. A strategy that only worked in calm conditions is fragile.
3. **Replay forensics.** Past breaches are often explained by turbulence crossing the threshold. The [Replay](/help/reference/pages/replay) page surfaces the turbulence value at decision time so you can see whether the throttle was active.

## Why the two mechanisms complement each other

Regime is a slow classifier — it changes over weeks. Turbulence is a fast detector — it can spike in a single session and decay over days. The combination gives the system a way to handle both kinds of shift:

- A new regime triggers a recalibration: the next backtest window includes the regime's data, the engine's policy is updated, the overlay caps are revisited.
- A turbulence spike triggers an immediate throttle: the *current* recommendation is de-risked, no waiting for the next training cycle.

## What this changes in your workflow

Three practical implications:

- When the regime chip shows a transition, expect the next few recommendations to drift away from the recent baseline. This is the engine adapting, not malfunctioning.
- When the turbulence index spikes, expect recommendations to look smaller, more cash-heavy, and more conservative. This is the overlay throttling, not the engine giving up.
- When evaluating a backtest, check the turbulence shading. A backtest with strong returns only in calm regimes is a backtest you should treat with caution.

## See also

- [Risk overlays](/help/concepts/risk-overlays) — the layer that consumes the turbulence index.
- [Known pitfalls](/help/concepts/known-pitfalls) — including reading a low-vol backtest as a universal result.
- [The weight-centric pipeline](/help/concepts/weight-centric-pipeline) — where the throttle sits.
