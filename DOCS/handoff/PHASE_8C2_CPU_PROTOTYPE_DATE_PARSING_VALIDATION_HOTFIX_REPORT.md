# Phase 8C.2: CPU Prototype Date Parsing Validation Hotfix

**Date:** 2026-04-26
**Status:** Complete

---

## Root Cause

Three FinRL-X endpoints (`train-cpu-prototype`, `validate-dataset`, `train-research`) parsed user-provided date strings with `date.fromisoformat()` outside a try/except. Malformed date values (e.g. `"not-a-date"`, `"31/12/2026"`) would raise an uncaught `ValueError` instead of returning HTTP 422.

## Endpoints Fixed

| Endpoint | Before | After |
|----------|--------|-------|
| `POST /rl/finrlx/train-cpu-prototype` | bare `date.fromisoformat()` | `_parse_date()` with 422 |
| `POST /rl/finrlx/validate-dataset` | bare `date.fromisoformat()` | `_parse_date()` with 422 |
| `POST /rl/finrlx/train-research` | bare `date.fromisoformat()` | `_parse_date()` with 422 |

## Exact Validation Behavior

Added `_parse_date(value, field_name)` helper in `rl_finrlx.py`:
- `None`/empty → returns `None` (optional dates)
- Valid ISO format → returns `date` object
- Invalid format → raises `HTTPException(422, "Invalid {field_name}. Expected YYYY-MM-DD.")`

Existing `start_date > end_date` check unchanged (422: "start_date must be <= end_date.").

## Files Changed

```
backend/app/api/v1/rl_finrlx.py           — added _parse_date helper, applied to all 3 endpoints
backend/tests/test_phase8c_cpu_prototype.py — 5 new date parsing tests
DOCS/handoff/PHASE_8C2_CPU_PROTOTYPE_DATE_PARSING_VALIDATION_HOTFIX_REPORT.md
```

## Tests Added

| Test | Validates |
|------|-----------|
| `test_cpu_prototype_invalid_start_date` | malformed start_date → 422 |
| `test_cpu_prototype_invalid_end_date` | malformed end_date → 422 |
| `test_validate_dataset_invalid_start_date` | validate-dataset malformed date → 422 |
| `test_train_research_invalid_start_date` | train-research malformed date → 422 |
| `test_invalid_date_does_not_create_candidate` | no candidate created on bad date |

## Backend Test Results

```
368 passed, 2 skipped — zero regressions
```

## Frontend Build Status

No frontend changes. Not touched.

## Design Handoff Review

No design changes. Reviewed in Phase 8C.1 — HANDOFF.md (authoritative spec), tokens.css/styles.css (OKLCH tokens), Design System.html, Ops.html all intact. No new UI surfaces added.

## Safety Confirmations

| Check | Status |
|-------|--------|
| No live RL added | CONFIRMED |
| No broker execution | CONFIRMED |
| No recommendation pollution | CONFIRMED |
| No overview pollution | CONFIRMED |
| No publication influence | CONFIRMED |
| No torch/gymnasium/stable-baselines3 installed | CONFIRMED |
| All outputs research/offline/shadow only | CONFIRMED |
| Existing Phase 8A/8B/8C tests pass | CONFIRMED |

## Production Smoke Commands

```bash
# Malformed date → 422
curl -s -X POST http://localhost:8000/api/v1/rl/finrlx/train-cpu-prototype \
  -H 'Content-Type: application/json' \
  -d '{"algorithm":"PPO","start_date":"bad","research_acknowledgement":true}'
# Expected: 422 "Invalid start_date. Expected YYYY-MM-DD."

# Valid dates still work
curl -s -X POST http://localhost:8000/api/v1/rl/finrlx/train-cpu-prototype \
  -H 'Content-Type: application/json' \
  -d '{"algorithm":"PPO","start_date":"2026-03-15","end_date":"2026-04-15","research_acknowledgement":true}' | jq .data.status

# Reversed dates → 422
curl -s -X POST http://localhost:8000/api/v1/rl/finrlx/train-cpu-prototype \
  -H 'Content-Type: application/json' \
  -d '{"algorithm":"PPO","start_date":"2026-04-15","end_date":"2026-03-15","research_acknowledgement":true}'
# Expected: 422 "start_date must be <= end_date."

# validate-dataset malformed → 422
curl -s -X POST http://localhost:8000/api/v1/rl/finrlx/validate-dataset \
  -H 'Content-Type: application/json' \
  -d '{"start_date":"abc"}'
# Expected: 422

# train-research malformed → 422
curl -s -X POST http://localhost:8000/api/v1/rl/finrlx/train-research \
  -H 'Content-Type: application/json' \
  -d '{"start_date":"xyz","research_acknowledgement":true}'
# Expected: 422
```

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | train-cpu-prototype invalid start_date returns 422 | PASS |
| 2 | train-cpu-prototype invalid end_date returns 422 | PASS |
| 3 | validate-dataset invalid start_date returns 422 | PASS |
| 4 | train-research invalid start_date returns 422 | PASS |
| 5 | start_date > end_date still returns 422 | PASS |
| 6 | malformed dates do not create candidates | PASS |
| 7 | dependency_unavailable path still validates dataset contract | PASS |
| 8 | train-cpu-prototype response still includes isolation_checks | PASS |
| 9 | CPU prototype audit tests still verify persisted AuditEvent rows | PASS |
| 10 | existing Phase 8A/8B/8C tests still pass | PASS |
| 11 | no real PPO/A2C claimed unless actually run | PASS |
| 12 | no torch/gymnasium/stable-baselines3 installed | PASS |
| 13 | no live RL added | PASS |
| 14 | no broker/execution functionality added | PASS |
| 15 | no recommendation/overview/publication pollution | PASS |
| 16 | backend tests pass (368 passed, 2 skipped) | PASS |
| 17 | frontend build passes if touched | N/A |
| 18 | design/handoff-package reviewed and documented | PASS |
