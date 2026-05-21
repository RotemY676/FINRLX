# Phase FX-3 — /paper Page Currency Toggle

**Date:** 2026-05-21
**Base commit:** `217048d` (FX-2)
**Track:** Phase FX — sub-phase 3 of 4.

## What this sub-phase ships

A small currency-valuation card injected into `/paper`. It shows the
active portfolio's total value in the user's chosen currency, with a
selector to switch, a "use profile" shortcut, and per-holding FX
transparency in an expandable details block.

| Artifact | Path |
|---|---|
| Card component | `frontend/src/features/wizard/CurrencyValuation.tsx` |
| Page injection | `frontend/src/app/paper/page.tsx` (1-line import + 1 component tag) |

## Behavior

1. On mount, the component calls `GET /api/v1/profile/me` and reads
   `profile.base_currency` (falls back to `USD` if no profile / not
   reachable). The selector defaults to that currency.
2. The user picks any of `USD / EUR / ILS / GBP`. Each change triggers
   `GET /api/v1/paper/current/valuation-in-currency?currency=…` and
   the card re-renders.
3. The card shows:
   * **Total value** in the selected currency, formatted via
     `Intl.NumberFormat`.
   * **"use profile"** link when the selector ≠ profile currency.
   * **FX warnings** from the meta envelope (any stale/cross/inverse
     paths) — visible via an `aria-live="polite"` status region.
   * **Banner** "Some rates used a fallback path…" when any holding
     used a non-exact-date rate.
   * **Expandable per-holding detail**: every position with native
     amount → target amount, the rate used, the rate date, and a
     "fallback" tag when applicable.
4. `404` from the endpoint (no active portfolio) is treated as an
   informational state, not an error — the UI degrades quietly.

## Why a separate component

`/paper` is a large existing page with its own state machine. Injecting
a 220-line CurrencyValuation card as a single component keeps the diff
to a 1-line import + 1 component tag, which is trivially revertable if
the operator decides FX isn't beta-1 priority.

## Gate results (verified locally, 2026-05-21)

| Gate | Result |
|---|---|
| Backend pytest | 892 (unchanged from FX-2) |
| Frontend tsc | clean |
| Frontend vitest | 27 (unchanged) |
| Frontend next build | OK; `/paper` 5.68 kB (was 4.0 kB; +1.68 kB) |
| Playwright `/paper` (desktop + mobile) | 2 passed |

## Follow-ups

* **FX-4** opens an Incident when the FX cache has no fresh row for
  >24h. The CurrencyValuation card's warnings will start to reflect
  this naturally once OP-2 schedules the daily refresh.
* If the user changes their profile currency, that update doesn't
  push to other open tabs — they need to refresh. Acceptable for the
  closed beta.
* No keyboard shortcut to cycle currencies. Easy to add but out of
  scope for this sub-phase.

## Honest limitations

* The component reads the JWT token directly from `localStorage`
  rather than going through `services/auth.ts`. Done to keep the
  component self-contained; it's the same storage key the rest of
  the app uses, so behaviorally equivalent. The next opportunity to
  consolidate auth helpers should also pull this in.
* `formatAmount` uses `Intl.NumberFormat` which may render with a
  currency symbol the user doesn't recognize (e.g. `₪` for ILS).
  We accept this as the standard browser behavior; users opting into
  a non-USD currency are expecting their local symbol.
* The card shows the most-recent prices in native currency and the
  most-recent FX rate independently. A date mismatch is invisible in
  the card itself but visible in the per-holding detail (each shows
  its `fx_rate_date`). Acceptable for medium-term investing.

## Sources

* (no new external sources beyond FX-1/FX-2)
