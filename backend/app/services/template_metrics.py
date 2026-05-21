"""Phase TPL-2 — expected-performance estimates for recommendation templates.

We don't run a live backtest engine per template here (too slow, depends
on data freshness). Instead we compute deterministic, methodology-backed
**estimates** from a 2-asset model (equity sleeve, defensive sleeve)
parametrized by published long-term assumptions.

Sources (cited in the surfaced ``methodology_note``):
* Vanguard 10-year capital-market assumptions (US equity ~6–8% nominal,
  US aggregate bonds ~3–4%).
* Morningstar long-term asset-class volatility tables (US equity σ≈16%,
  US aggregate bonds σ≈5%).
* Historical equity / bond correlation ranges 0.0–0.2.

Estimates are flagged with a ``confidence_label`` of "low" — these are
order-of-magnitude planning numbers, not backtested values. The
``/templates`` UI surfaces the label + methodology note explicitly so
the user is never misled into thinking these are realized returns.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from app.models.recommendation_template import RecommendationTemplate
from app.services.profile_mapping import derive_allocation

# ── Published long-term assumptions ──────────────────────────────────


EQUITY_EXPECTED_RETURN = 0.07      # 7% nominal annual
EQUITY_VOLATILITY = 0.16           # 16% annualized
DEFENSIVE_EXPECTED_RETURN = 0.035  # 3.5% nominal annual
DEFENSIVE_VOLATILITY = 0.05        # 5% annualized
ASSET_CORRELATION = 0.10           # 10% — equity vs aggregate bond proxy
RISK_FREE_RATE = 0.04              # 4% — consistent with current short Treasury yields

# Max-drawdown is approximated as ~2.5 × annualized volatility (Calmar
# rule-of-thumb for diversified long-only equity portfolios; trims to
# the user-specified cap if the methodology number exceeds it).
MAX_DRAWDOWN_MULTIPLIER = 2.5

METHODOLOGY_NOTE = (
    "Estimates derived from a 2-asset model (equity / defensive) using "
    "published Vanguard 10-yr CMA + Morningstar long-term σ. These are "
    "order-of-magnitude planning numbers, NOT backtested results."
)


@dataclass(frozen=True)
class TemplateMetrics:
    equity_pct: float
    defensive_pct: float
    expected_annual_return_pct: float
    expected_volatility_pct: float
    expected_max_drawdown_pct: float
    sharpe_estimate: float
    confidence_label: str
    methodology_note: str


def _portfolio_expected_return(equity_pct: float, defensive_pct: float) -> float:
    e, d = equity_pct / 100.0, defensive_pct / 100.0
    return e * EQUITY_EXPECTED_RETURN + d * DEFENSIVE_EXPECTED_RETURN


def _portfolio_volatility(equity_pct: float, defensive_pct: float) -> float:
    e, d = equity_pct / 100.0, defensive_pct / 100.0
    var = (
        (e * EQUITY_VOLATILITY) ** 2
        + (d * DEFENSIVE_VOLATILITY) ** 2
        + 2 * e * d * EQUITY_VOLATILITY * DEFENSIVE_VOLATILITY * ASSET_CORRELATION
    )
    return math.sqrt(var)


def expected_metrics(template: RecommendationTemplate) -> TemplateMetrics:
    """Return order-of-magnitude planning metrics for a template.

    Honors the user's stated ``max_drawdown_pct`` cap: if the
    methodology number exceeds the cap, we report the cap (this is what
    the Risk Overlay would enforce in production).
    """
    targets = derive_allocation(template.risk_bucket, template.horizon_band)
    equity_pct = targets.equity_pct
    defensive_pct = targets.defensive_pct

    ret = _portfolio_expected_return(equity_pct, defensive_pct)
    vol = _portfolio_volatility(equity_pct, defensive_pct)

    raw_max_dd = vol * MAX_DRAWDOWN_MULTIPLIER * 100.0  # to %
    capped_max_dd = min(raw_max_dd, template.max_drawdown_pct)

    excess = ret - RISK_FREE_RATE
    sharpe = excess / vol if vol > 0 else 0.0

    return TemplateMetrics(
        equity_pct=equity_pct,
        defensive_pct=defensive_pct,
        expected_annual_return_pct=round(ret * 100.0, 2),
        expected_volatility_pct=round(vol * 100.0, 2),
        expected_max_drawdown_pct=round(capped_max_dd, 2),
        sharpe_estimate=round(sharpe, 2),
        confidence_label="low",
        methodology_note=METHODOLOGY_NOTE,
    )
