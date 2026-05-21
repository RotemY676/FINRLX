---
title: Metrics
summary: Sharpe, Sortino, Calmar, max drawdown, turnover — formulas and gotchas.
diataxis: reference
area: reference
updated: 2026-05-22
order: 3
---

FINRLX reports a small, opinionated set of performance metrics. Each metric captures one specific risk-adjusted attribute of a strategy. Reading them in isolation is misleading; reading them together is informative.

## Sharpe ratio

The most-used risk-adjusted return metric.

**Formula:**

```
Sharpe = (mean(R) - R_f) / std(R) × sqrt(P)
```

where `R` is the periodic return series, `R_f` is the risk-free rate over the same period, `std` is the sample standard deviation, and `P` is the periods-per-year scaling factor (252 for daily returns, 12 for monthly).

**What it rewards.** Steady returns with low volatility in either direction.

**Common misreading.** Sharpe penalizes *all* volatility, including upside moves. A strategy with strong positive skew (occasional big wins, small losses) can score lower than a steady mediocre strategy. Use Sortino as a complement.

**Rule of thumb.** Sharpe > 1 is good for a single strategy on a single regime; Sharpe > 2 is exceptional and should make you check for [overfitting](/help/concepts/known-pitfalls#backtest-overfitting).

## Sortino ratio

Like Sharpe but penalizes only downside volatility.

**Formula:**

```
Sortino = (mean(R) - R_f) / downside_std(R) × sqrt(P)

where downside_std(R) = sqrt( mean( min(R - R_target, 0)^2 ) )
```

`R_target` is the minimum acceptable return — typically the risk-free rate or zero. Sortino is always greater than or equal to Sharpe for the same series.

**What it rewards.** Returns with low *downside* volatility, regardless of upside variability.

**Common misreading.** Sortino can be much higher than Sharpe when the strategy is positively skewed — this is real and worth reading. But it can also reflect an artifact of low downside-sample count: in a backtest with very few losing periods, the denominator is small and Sortino balloons. Always check the count of negative returns alongside.

## Calmar ratio

Annualized return divided by maximum drawdown.

**Formula:**

```
Calmar = annualized_return / |max_drawdown|
```

The maximum drawdown is the largest peak-to-trough decline observed in the equity curve.

**What it rewards.** Strategies that produce steady gains without large drawdowns.

**Common misreading.** Calmar is heavily dependent on the single worst drawdown event in the window. A backtest that happens to *miss* a particular drawdown window scores enormously; the same backtest with a different start date will score very differently. Always look at the drawdown distribution, not the headline number.

## Maximum drawdown

The largest peak-to-trough decline in portfolio value over the evaluation window.

**Formula:**

```
DD(t) = (V(t) - max_{s ≤ t} V(s)) / max_{s ≤ t} V(s)
max_drawdown = min_t DD(t)
```

Always reported as a negative number or as an absolute percentage.

**What it tells you.** The worst loss a holder of this strategy would have experienced. Equivalently, the loss you would have wanted to liquidate at — if you could not stomach.

**Common misreading.** Max drawdown is one observation, not a distribution. A strategy with -15% max drawdown over 5 years says nothing about whether it would have -15% again. Look at the drawdown duration (peak to recovery), not just depth, and look at the second-worst drawdown to ground the headline.

## Turnover

The fraction of the portfolio traded per period.

**Formula:**

```
turnover(t) = sum( |weight(t) - weight(t-1)| ) / 2
```

Divided by 2 because every dollar that leaves one name enters another. Annualized turnover is computed by summing per-period turnover and scaling.

**What it tells you.** How active the strategy is. High turnover amplifies cost drag.

**Common misreading.** Low turnover is not automatically good — a buy-and-hold has turnover zero but cannot adapt to regime shifts. The right reading is "turnover *relative to* the return premium you are getting": Sharpe-per-unit-turnover is a more honest yardstick.

## Volatility

Annualized standard deviation of returns.

**Formula:**

```
vol = std(R) × sqrt(P)
```

Same scaling logic as Sharpe.

**What it tells you.** How dispersed the return distribution is. Combined with mean return, it specifies the bulk of the strategy's risk profile.

## How FINRLX renders these

Every backtest displays Sharpe, Sortino, Calmar, max drawdown, and turnover. The Paper portfolio displays the same metrics, recomputed over the live-paper window. The Replay page exposes the metrics as they were *at the moment of decision*, so you can see how the picture has evolved since.

Sortino, Calmar, and max drawdown all depend on having enough data to identify a meaningful drawdown — usually 250+ trading days. With shorter windows, treat them as suggestive rather than definitive.

## See also

- [Backtest vs. paper vs. live](/help/concepts/backtest-vs-paper-vs-live) — where to compare these numbers.
- [Backtests](/help/reference/pages/backtests) — the page that renders them at scale.
- [Known pitfalls](/help/concepts/known-pitfalls) — why high metrics demand skepticism, not celebration.
