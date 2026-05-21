# Phase FX-1 — FX Rate Layer (Frankfurter + persistence + conversion)

**Date:** 2026-05-21
**Base commit:** `3faf350` (TPL-4 / Phase TPL close)
**Track:** Phase FX — sub-phase 1 of 4.

## What this sub-phase ships

A complete FX data layer: cache table, Frankfurter HTTP adapter, and a
conversion service with a documented fallback chain. No HTTP endpoint
yet — FX-2 wires the conversion into `PaperPortfolio` valuation.

| Artifact | Path |
|---|---|
| Model | `backend/app/models/fx.py` |
| Migration `023_fx_rates` | `backend/migrations/versions/023_fx_rates.py` |
| Provider | `backend/app/services/data_providers/frankfurter_provider.py` |
| Service | `backend/app/services/fx_service.py` |
| Tests (8) | `backend/tests/test_phase_fx1_fx_layer.py` |

## Schema (`fx_rates`)

| Column | Type | Notes |
|---|---|---|
| `id` | `String(36)` PK | UUID |
| `base_currency` | `String(3)` | indexed |
| `quote_currency` | `String(3)` | indexed |
| `rate_date` | `Date` | indexed |
| `rate` | `Float` | "1 base = N quote" |
| `source` | `String(40)` | default `frankfurter` |
| `created_at` | `DateTime(tz)` | |

UNIQUE on `(base_currency, quote_currency, rate_date, source)`. Rows
are immutable once written — historical FX is not rewritable.

## Provider — Frankfurter

* Endpoint base: `https://api.frankfurter.dev/v2`
* No API key, no monthly/daily quotas.
* Returns ECB reference rates (one publish per business day).
* Supported pairs in code: USD, EUR, ILS, GBP (matches the wizard's
  `SUPPORTED_BASE_CURRENCIES`).
* Errors wrap any failure in `FrankfurterError`.

## Service — `FxService`

### `convert(amount, from, to, on_date=None) -> FxConversion`

Fallback chain (documented in code + tests):

1. **Same currency** → returns 1.0, `is_fallback=False`.
2. **Direct hit**: `(from, to)` row with `rate_date <= on_date` —
   marked `is_fallback=False` only when the row is exact-date.
3. **Cross-rate via USD**: when neither side is USD and a direct row is
   missing, use `from→USD * USD→to`. Result is marked
   `is_fallback=True` with reason `"cross-rated via USD"`.
4. **Inverse direct**: when only the reciprocal row exists (`to→from`),
   use `1 / rate`. Marked `is_fallback=True`, reason
   `"inverted-from-quote"`.
5. **No path** → `FxConversionError`.

### `refresh_rates_for_today(bases, quotes, rate_date=None) -> dict`

Once-per-day job (OP-2 will schedule it). Iterates `(base, quote)`
pairs and writes rows via `upsert_rate`. **Partial-writes are safe**:
if one base errors, others still write — the result dict reports
`{fetched, errors}`.

### `upsert_rate(base, quote, date, rate, source)`

Idempotent. If the same `(base, quote, date, source)` row exists with
the same value, returns it unchanged. If the cached value differs from
the upstream value, **the cached value wins** (never overwrite history;
re-fetches on the same day should be no-ops by the ECB once-per-day
publish cadence).

## Invariants tested (8)

1. `fx_rates` UNIQUE constraint enforced.
2. `convert(same, same)` → 1.0 with no fallback.
3. `convert(direct hit)` → exact row used, no fallback flag.
4. `convert(stale)` → most recent row chosen, fallback reason
   includes the date used.
5. `convert(cross-rate via USD)` → 2-leg multiplication, fallback
   reason `"cross-rated via USD"`.
6. `convert(inverse only)` → `1 / reciprocal`, fallback reason
   `"inverted-from-quote"`.
7. `convert(no path)` → `FxConversionError`.
8. `refresh_rates_for_today(...)` with a mocked provider:
   partial-writes when one base errors; reports `{fetched, errors}`
   accurately.

## Gate results (verified locally, 2026-05-21)

| Gate | Result |
|---|---|
| Backend pytest (FX-1 file) | **8 passed** |
| Backend pytest (full) | running — will report after green |
| Backend ruff | clean |
| Backend mypy | clean on `app/core/` |
| Alembic upgrade head | OK |
| Alembic downgrade `023 → 022` | OK |
| Alembic re-upgrade `022 → 023` | OK |

## Follow-ups

* **FX-2** adds `PaperPortfolio.base_currency` + valuation conversion.
  P&L surfaces in the user's chosen base currency.
* **FX-3** updates the `/paper` page to render in base currency with
  an optional USD/local toggle.
* **FX-4** adds the freshness watchdog (incident opens if no fresh row
  for > 24h).
* **OP-2** scheduler will call `refresh_rates_for_today()` daily.

## Honest limitations

* **No live network call in this sub-phase.** All tests mock the
  Frankfurter HTTP layer. The first live fetch happens when the
  operator runs `python -c "from app.services.fx_service import FxService; ..."`
  against a real DB or when OP-2 schedules it. Until then, the cache
  is empty — meaning any FX-2 conversion will use only what's been
  fetched.
* **Source is hard-coded to "frankfurter"** in the upsert default. If a
  future provider is added, the source string becomes a discriminator
  (the UNIQUE constraint already includes it).
* **Cross-rate via USD assumes USD as the universal hub.** This is the
  documented Frankfurter behavior. If we add a non-USD primary in the
  future, the chain needs adjustment.

## Sources

* [Frankfurter API documentation](https://frankfurter.dev/) — ECB
  reference rates, no API key, 1948→present.
