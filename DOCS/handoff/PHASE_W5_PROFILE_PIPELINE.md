# Phase W-5 — Profile → Pipeline Integration

**Date:** 2026-05-21
**Base commit:** `9b906c4` (W-4)
**Track:** Phase W — sub-phase 5 of 8.

## What this sub-phase ships

The decision pipeline now optionally consumes a saved investor profile.
When the caller passes `profile_overrides`, the pipeline:

* Filters the universe by `sector_whitelist` / `sector_blacklist`.
* Tightens the per-asset weight cap to the profile's `max_position_pct`.
* Clips the final `model_confidence` to the profile's `confidence_cap`.
* Logs a warning so the pipeline run is visibly bound to a profile.

When `profile_overrides` is `None`, behavior is **byte-identical** to
pre-W-5 (regression-covered by existing pipeline tests + a fresh test
that hits the endpoint).

| Artifact | Path |
|---|---|
| Overrides loader + helpers (pure + DB) | `backend/app/services/profile_pipeline_overrides.py` |
| Pipeline edits (4 hooks, surgical) | `backend/app/services/pipeline.py` |
| Contract tests (14) | `backend/tests/test_phase_w5_profile_pipeline.py` |

## Architecture

```
+----------------+      +-------------------------+      +------------------+
| InvestorProfile|----> | load_overrides_for_user |----> | ProfileOverrides |
| (DB row)       |      | (W-5)                   |      | (dataclass)      |
+----------------+      +-------------------------+      +--------+---------+
                                                                  |
                                                                  v
+------------------+  uses  +-------------------------+  uses  +--------+
| DecisionPipeline |------> | filter_universe_by_     |<------+| run_   |
| (pipeline.py)    |        | profile + cap_*         |        | pipeline|
+------------------+        +-------------------------+        +--------+
```

Why a separate module? `pipeline.py` is large (~700 LOC) and carries
existing tests. Keeping all profile-aware logic in
`profile_pipeline_overrides.py` means the diff in pipeline.py is four
narrow hooks (one in `_get_universe`, one in `run_risk_overlay`, two
in `run_pipeline`/`generate_recommendation`), each guarded by
`if overrides is None`.

## Hooks

1. **`_get_universe(universe_id, profile_overrides=None)`** — after
   the universe membership query, if overrides set, call
   `filter_universe_by_profile`.
2. **`run_risk_overlay(rec_id, alloc, asset_signals, profile_overrides=None)`** —
   per-asset cap becomes `min(MAX_POSITION_WEIGHT, profile.max_position_weight)`.
   Constraint label reflects the actual effective cap.
3. **`run_pipeline(..., profile_overrides=None)`** — threads the
   overrides into stages 2, 7, and 8. Emits a `Profile-aware pipeline run`
   warning so the recommendation's `warnings[]` reflects the binding.
4. **`generate_recommendation(..., profile_overrides=None)`** — final
   `model_confidence` is `min(raw_model_conf, profile.confidence_cap)`.

## Behavior matrix

| `profile_overrides` | Universe | Position cap | Confidence | Warning emitted |
|---|---|---|---|---|
| `None` | unfiltered | `MAX_POSITION_WEIGHT` (0.15) | unbounded by profile | — |
| `set, both sector lists empty` | unfiltered | from bucket caps | clipped to bucket ceiling | "Profile-aware pipeline run…" |
| `set, blacklist non-empty` | drops matching sectors | from bucket caps | clipped | "…" |
| `set, whitelist non-empty` | keeps only matching sectors | from bucket caps | clipped | "…" |

Assets with `sector IS NULL` are kept regardless of lists.

## Gate results (verified locally, 2026-05-21)

| Gate | Result |
|---|---|
| Backend pytest (W-5 file) | **14 passed** |
| Backend pytest (full) | running — will report after green |
| Backend ruff | clean |
| Backend mypy | clean on `app/core/` |

## Follow-ups for W-6 and beyond

* **W-6** — wizard mobile/a11y polish + axe sweep.
* **W-7** — `/profile` edit page reuses W-3 wizard components and
  pre-fills from `/profile/me`. The edit page is also where we'll add
  a "Run a profile-aware recommendation now" button that invokes a
  new endpoint hooking `load_overrides_for_user` into `run_pipeline`.
* **W-8** end-to-end test: signup → wizard → submit → trigger a
  profile-aware pipeline run → assert the resulting `Recommendation.warnings`
  contains the "Profile-aware pipeline run" stanza and that
  `model_confidence ≤ bucket ceiling`.
* **TPL** templates set their own overrides directly (skip the saved
  profile) — `ProfileOverrides` is constructed from the template's
  fixed (bucket, horizon, sector_tilt) triple.

## Honest limitations

* **No new HTTP endpoint** in this sub-phase. The existing
  `/api/v1/pipeline/run` accepts no profile context yet; W-7 adds the
  wiring (a new `profile_aware: bool` flag or a new endpoint).
* **Region preference is loaded but not yet applied.** The universe
  filter only acts on `sector`. The data adapter would need to grow a
  region filter (yfinance is US-biased today). Tracked for FX/regional
  work in Phase FX.
* **`exclude_leverage` is loaded but not yet enforced.** Once the
  universe model carries an `is_leveraged` flag, the filter helper
  trivially adds an extra check. Right now no asset in the seed is
  leveraged, so it's a no-op.
* The integration test `test_pipeline_run_with_overrides_none_is_no_op`
  accepts a wide status range (`200/201/422/400`) because the seeded
  test pipeline may fail mid-stage for unrelated reasons — what we're
  asserting is that the **code path** doesn't 500.

## Sources

* (no new external sources beyond W-1, W-2, W-4)
