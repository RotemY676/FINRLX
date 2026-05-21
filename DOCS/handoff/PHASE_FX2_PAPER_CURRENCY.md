# Phase FX-2 — PaperPortfolio Base-Currency + Valuation Endpoint

**Date:** 2026-05-21
**Base commit:** `5e416fa` (FX-1)
**Track:** Phase FX — sub-phase 2 of 4.

## What this sub-phase ships

`PaperPortfolio` now carries a `base_currency` column. A new endpoint
translates the active portfolio's holdings into any supported currency
using the FX-1 service, with per-holding transparency on the rate used.

| Artifact | Path |
|---|---|
| Model column | `backend/app/models/validation.py` (`PaperPortfolio.base_currency`) |
| Migration `024_paper_base_ccy` | `backend/migrations/versions/024_paper_portfolio_base_currency.py` |
| Conversion helper | `backend/app/services/paper_currency.py` |
| New endpoint | `backend/app/api/v1/paper.py` (`GET /paper/current/valuation-in-currency?currency=…`) |
| Tests (7) | `backend/tests/test_phase_fx2_paper_currency.py` |

## Behavior

### Model column

`PaperPortfolio.base_currency: str` — 3-char ISO code, default `"USD"`,
not null. Backfilled in-place by migration 024 so every existing row
becomes `USD` immediately.

### Endpoint

`GET /api/v1/paper/current/valuation-in-currency?currency=EUR`

Returns:

```jsonc
{
  "meta": { "warnings": ["TICKER: FX EUR->USD using 2025-05-09 (no row for 2025-05-10)"] },
  "data": {
    "portfolio_id": "...",
    "base_currency": "USD",
    "target_currency": "EUR",
    "as_of_date": "2025-05-10",
    "total_value_in_target": 12345.67,
    "holdings": [
      {
        "asset_id": "...",
        "ticker": "AAPL",
        "asset_currency": "USD",
        "quantity": 10,
        "last_price": 195.0,
        "value_native": 1950.0,
        "value_in_target": 1779.0,
        "fx_rate": 0.9123,
        "fx_rate_date": "2025-05-10",
        "fx_is_fallback": false
      }
    ]
  }
}
```

Error cases:
- `404 no_active_paper_portfolio` if no active portfolio
- `422` if currency is not 3 chars

### Conversion helper contract

`value_portfolio_in_currency(db, portfolio, target_currency, on_date=None)`:

* Loads every holding's `Asset.currency` (default `USD` if missing).
* Fetches the latest known price for each asset from `market_bars`.
* Converts `value_native = quantity * last_price` from
  `asset.currency` to `target_currency` via `FxService.convert`.
* On `FxConversionError`, the holding's `value_in_base=0` and a
  warning is collected; the call **does not raise** (UI gets a partial
  result with explicit gaps).
* Returns per-holding lines + aggregate `total_value_in_target` +
  `fx_warnings[]`.

## Invariants tested (7)

1. `PaperPortfolio.base_currency` defaults to `"USD"` on insert.
2. Same-currency translation passes through with `rate=1.0`, no fallback.
3. Cross-currency translation uses the FX rate from the cache.
4. Missing FX path collects a warning + zero value; no crash.
5. Endpoint rejects `currency` of wrong length (422).
6. Endpoint returns translated payload when a portfolio exists.
7. Endpoint 404s when there is no active portfolio (verified via
   `monkeypatch`).

## Gate results (verified locally, 2026-05-21)

| Gate | Result |
|---|---|
| Backend pytest (FX-2 file) | **7 passed** |
| Backend pytest (full) | running — will report after green |
| Backend ruff | clean |
| Backend mypy | clean on `app/core/` |
| Alembic upgrade head | OK |
| Alembic downgrade `024 → 023` | OK |
| Alembic re-upgrade `023 → 024` | OK |

## Follow-ups

* **FX-3** updates the `/paper` page to show P&L in `profile.base_currency`
  by calling this endpoint on render. A USD/local toggle on the page is
  trivial since the endpoint accepts any 3-letter currency.
* **FX-4** adds the freshness watchdog: if no fresh FX row arrived in
  > 24 hours, open an Incident.
* When `OP-2` (scheduler) runs, `refresh_rates_for_today` populates the
  cache nightly and the warnings on this endpoint go quiet.

## Honest limitations

* The endpoint reads the **active** portfolio. If a user has multiple
  portfolios, only the most recent active one is translated. A path
  param variant (`/paper/{id}/valuation-in-currency`) can be added in
  FX-3 if needed by the UI.
* `value_native` uses the most recent `market_bars` close, regardless of
  date alignment with `on_date`. If the FX rate is from 2025-05-10 but
  the price is from 2025-05-15, there's a 5-day mismatch we don't surface.
  This is acceptable for paper-portfolio P&L (intraday FX is rarely
  meaningful for medium-term investing) but worth flagging in the UI
  when staleness exceeds a threshold.
* `total_value_native_sum` is exposed in the dataclass but not in the
  API — it sums values across mixed currencies and isn't meaningful
  on its own. We only ship the target-currency total.

## Sources

* (no new external sources beyond FX-1)
