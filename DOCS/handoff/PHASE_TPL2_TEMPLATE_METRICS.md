# Phase TPL-2 — Template Expected-Metrics Service + Read API

**Date:** 2026-05-21
**Base commit:** `f41732b` (TPL-1)
**Track:** Phase TPL — sub-phase 2 of 4.

## What this sub-phase ships

A deterministic expected-metrics service (CAGR estimate, vol estimate,
max DD estimate, Sharpe estimate) per template, plus 2 read endpoints
that surface them.

| Artifact | Path |
|---|---|
| Metrics service (pure) | `backend/app/services/template_metrics.py` |
| Response schemas | `backend/app/schemas/template.py` |
| API endpoints | `backend/app/api/v1/templates.py` |
| Router registration | `backend/app/api/router.py` |
| Tests (9) | `backend/tests/test_phase_tpl2_template_metrics.py` |

## API additions

| Method | Path | Returns |
|---|---|---|
| GET | `/api/v1/templates` | active templates, seeds first, with embedded metrics |
| GET | `/api/v1/templates/{key}` | one template by slug or `404` |

Both require auth. Embedded `metrics` field uses
`TemplateMetricsResponse` (8 fields including `confidence_label` and
`methodology_note`).

## Metrics methodology

Two-asset model (equity sleeve, defensive sleeve) using published
long-term assumptions:

| Parameter | Value | Source |
|---|---|---|
| Equity expected return | 7% nominal | Vanguard 10-yr CMA range 6–8% |
| Equity volatility | 16% annualized | Morningstar US-equity long-term σ |
| Defensive expected return | 3.5% nominal | Vanguard 10-yr CMA US Agg bonds 3–4% |
| Defensive volatility | 5% annualized | Morningstar US Agg long-term σ |
| Equity-bond correlation | 0.10 | historical 0.0-0.2 range |
| Risk-free rate | 4.0% | short Treasury yields, 2026 |
| Max-drawdown approx | 2.5 × annualized σ | Calmar rule-of-thumb |

Formula: standard 2-asset portfolio variance with weighted means.
Output is clipped to the template's stated `max_drawdown_pct` (this is
the cap that the Risk Overlay would enforce in production).

**Honesty:** every response carries `confidence_label="low"` and a
methodology note. These are planning numbers, not backtested values.
TPL-3 will surface the label + note explicitly on each template card.

## Invariants tested

1. Pure low/high bucket return ordering: aggressive > conservative.
2. Conservative + 1y_3y → matches the exact 20/80 weighted return.
3. Max-DD cap: methodology number ≥ template cap → reported value
   equals template cap.
4. Sharpe positive (equity return > RF) and bounded `(-2, 2)`.
5. Methodology note mentions Vanguard + Morningstar (drift guard for
   the cited sources).
6. API requires auth; returns ≥ 5 templates with embedded metrics.
7. `/templates/tech_growth` returns the seed with Technology in
   whitelist + aggressive bucket.
8. `/templates/unknown` returns 404.
9. Each returned metrics has `equity_pct + defensive_pct == 100` and
   `expected_max_drawdown_pct <= template.max_drawdown_pct`.

## Gate results (verified locally, 2026-05-21)

| Gate | Result |
|---|---|
| Backend pytest (TPL-2 file) | **9 passed** |
| Backend pytest (full) | running — will report after green |
| Backend ruff | clean |
| Backend mypy | clean on `app/core/` |

## Follow-ups

* **TPL-3** ships the `/templates` page consuming `GET /templates`
  with cards rendering: name, badge, allocation_summary, description,
  metrics (equity %, expected return, max DD cap, Sharpe), confidence
  label, methodology link.
* **TPL-4** adds admin CRUD for user-authored templates (uses the
  existing role gate; `is_seed=False`).
* When the live `/api/v1/backtests/run` endpoint can run reliably
  against the live data layer (post OP-2 scheduler), `last_evaluated_at`
  + a real backtest summary can replace the methodology estimates.
  Until then the planning estimates are deliberately conservative.

## Honest limitations

* These are **not realized returns.** They are forward planning numbers.
  A regulator or sophisticated user would correctly mark them as
  assumptions. We surface `confidence_label="low"` and a multi-source
  methodology note to make this unmistakable.
* The same two assumption tables (equity / defensive) drive every
  template; differentiation comes from the allocation split + sector
  tilt — not from sector-specific return assumptions. A future
  refinement could add a sector-tilt premium when historical data
  supports it (e.g. Tech long-term return ≠ broad equity).
* Max-DD multiplier (`2.5 × σ`) is a rule-of-thumb. Empirical drawdowns
  vary widely with regime. The template's user-set cap is the binding
  guarantee in the Risk Overlay; the methodology number is informational.

## Sources

* [Vanguard 10-year capital-market assumptions](https://corporate.vanguard.com/content/corporatesite/us/en/corp/articles/vanguard-economic-and-market-outlook.html) (long-term equity ~6-8%, agg bonds ~3-4%)
* [Morningstar — long-term asset-class volatility](https://www.morningstar.com/portfolios/best-investment-portfolio-examples-savers-retirees)
* [Investopedia — Calmar ratio / max DD heuristics](https://www.investopedia.com/terms/c/calmarratio.asp)
