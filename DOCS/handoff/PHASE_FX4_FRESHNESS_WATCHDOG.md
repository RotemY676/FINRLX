# Phase FX-4 — FX Freshness Watchdog (closes Phase FX)

**Date:** 2026-05-21
**Base commit:** `3a204ee` (FX-3)
**Track:** Phase FX — sub-phase 4 of 4 (closes Phase FX).

## What this sub-phase ships

A pure freshness evaluator + an idempotent incident emitter. Together
they detect stale FX rates in the local cache and open Incident rows
that the existing `/ops/incidents` surface already renders.

| Artifact | Path |
|---|---|
| Evaluator + emitter | `backend/app/services/fx_freshness.py` |
| Runnable script | `backend/scripts/fx_freshness_watchdog.py` |
| Tests (7) | `backend/tests/test_phase_fx4_freshness_watchdog.py` |

## Functions

### `evaluate_freshness(db, threshold_hours=48, now=None) -> FxFreshnessReport`

Walks `fx_rates`, computes the latest publish moment per `(base, quote)`
(date-only rows are translated to 18:00 UTC, matching the ECB publish
window), and returns:

```python
@dataclass
class FxFreshnessReport:
    evaluated_at: datetime
    threshold_hours: float
    pairs: list[PairFreshness]      # all pairs
    stale_pairs: list[PairFreshness] # subset where age > threshold
```

Pure relative to `now` — tests pass an explicit `now` for determinism.

### `emit_incidents_if_stale(db, report) -> {opened, skipped_existing}`

* Pre-fetches all currently-open `Incident.title LIKE "FX stale: %"`
  rows in one query (avoids N+1).
* For each stale pair, if no open incident already covers
  `"FX stale: <base>-><quote>"` (prefix match — the trailing lag
  changes each run), opens a new one.
* Severity scales with age:
  - `≤ 72h` → severity 3 (warning)
  - `≤ 168h` (1 week) → severity 2 (high)
  - `> 168h` → severity 1 (critical)
* Idempotent: a second run within the same window doesn't duplicate.

### CLI

```
python -m scripts.fx_freshness_watchdog [--threshold 48]
```

Prints: `evaluated_pairs=N stale_pairs=M opened=K skipped_existing=L`.
Exits 0 regardless — the watchdog is observational, not blocking.

## Invariants tested (7)

1. Empty cache → empty report (no false-positive incidents).
2. A row older than the threshold is flagged stale; a fresh row isn't.
3. The most recent row per `(base, quote)` wins, even with multiple
   rows for the same pair.
4. Multiple stale pairs open one incident each.
5. Re-running the emitter doesn't duplicate incidents
   (`opened=0, skipped_existing=N`).
6. Severity scales correctly across the age buckets.
7. `PairFreshness` dataclass is frozen.

## Gate results (verified locally, 2026-05-21)

| Gate | Result |
|---|---|
| Backend pytest (FX-4 file) | **7 passed** |
| Backend pytest (full) | running — will report after green |
| Backend ruff | clean |
| Backend mypy | clean on `app/core/` |

## Phase FX — ledger

| Sub | Title | Commit | New tests |
|---|---|---|---|
| FX-1 | fx_rates table + Frankfurter adapter + conversion | `5e416fa` | 8 |
| FX-2 | PaperPortfolio.base_currency + valuation endpoint | `217048d` | 7 |
| FX-3 | /paper currency toggle + per-holding FX detail | `3a204ee` | (FE-only) |
| FX-4 | freshness watchdog + incident emission | this commit | 7 |

**Phase FX total**: 4 sub-phases, 22 new backend tests, 1 FE component
(CurrencyValuation), 1 new endpoint (`/paper/current/valuation-in-currency`),
1 new DB table (`fx_rates`), 1 column added (`paper_portfolios.base_currency`),
1 new CLI (`scripts.fx_freshness_watchdog`).

## Follow-ups

* **OP-2** scheduler will call `FxService.refresh_rates_for_today()`
  once per day and `evaluate_freshness + emit_incidents_if_stale`
  once per hour. Until then, run them manually.
* The watchdog only opens new incidents. **Resolution** still depends
  on whoever clears or acknowledges the incident via the existing
  `/ops/incidents` flow. A future small commit can auto-resolve when
  the next successful refresh restores the pair's freshness.
* No notification channel yet (email / Slack / webhook). OP-3's
  alerting service will pick up new Incidents and route them — same
  contract as `data_freshness` / policy breaches will use.

## Honest limitations

* `evaluate_freshness` treats the ECB publish moment as "rate_date +
  18:00 UTC". This is a heuristic; the actual ECB publish time
  is around 16:00 CET (15:00–16:00 UTC depending on DST). The
  18:00 figure gives us a small safety margin so a fresh row from
  earlier today doesn't get flagged stale by an over-pedantic clock
  check.
* If two providers ever publish the same pair on the same date
  (`source` differs), `evaluate_freshness` collapses them into one
  latest-row — it doesn't currently surface "this pair is stale at
  Frankfurter but fresh at provider X". Easy to extend; not needed
  for the closed beta.
* Incident `description` includes a "run this CLI" hint — useful for
  the operator, but the CLI itself doesn't fix anything (Frankfurter
  has to publish first). The hint is honest about that.

## Sources

* [ECB FX reference rates publishing schedule](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html)
* [Frankfurter API documentation](https://frankfurter.dev/)
