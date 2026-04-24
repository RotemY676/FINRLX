# Phase 4D: Decision Pipeline Core — Implementation Report

**Date:** 2026-04-24
**Phase:** 4D — Decision Pipeline Core
**Status:** Complete
**Method:** DOCS-driven development per Doc 21 playbook. No frontend changes.

---

## 1. Files Changed

### Created (6)
```
backend/app/services/pipeline.py                — DecisionPipelineService (selection, allocation, timing, risk, recommendation)
backend/app/schemas/pipeline.py                 — PipelineRunRequest/Result, PipelineStatusResponse
backend/app/api/v1/pipeline.py                  — 3 pipeline endpoints
backend/migrations/versions/006_recommendation_lineage.py — source_feature_set_id + source_signal_run_ids on recommendations
backend/tests/test_phase4d_pipeline.py          — 11 pipeline tests
DOCS/handoff/PHASE_4D_DECISION_PIPELINE_REPORT.md
```

### Modified (6)
```
backend/app/models/recommendation.py  — added source_feature_set_id, source_signal_run_ids
backend/app/schemas/__init__.py       — registered pipeline schemas
backend/app/api/router.py             — registered pipeline_router
backend/seed.py                       — run pipeline after engine run
```

---

## 2. Tables Reused / Modified

| Table | Change |
|---|---|
| `recommendations` | **MODIFIED** (migration 006) — added `source_feature_set_id`, `source_signal_run_ids` |
| `recommendation_weights` | Reused as-is |
| `selection_runs` | Reused as-is |
| `allocation_results` | Reused as-is |
| `timing_results` | Reused as-is |
| `risk_overlay_results` | Reused as-is |

**Total tables:** 28 (unchanged count, 1 modified)

---

## 3. Endpoints Added

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/pipeline/run` | Trigger full pipeline: signals → selection → allocation → timing → risk → recommendation |
| GET | `/api/v1/pipeline/status` | Pipeline status summary |
| GET | `/api/v1/pipeline/latest` | Latest pipeline-generated recommendation with weights |

**Total endpoints:** 52 (was 49)

---

## 4. Pipeline Stage Logic

### Selection
- Groups signal_outputs by asset
- Computes aggregate score: `buy=+1, hold=0, trim=-0.5, sell=-1`, weighted by confidence
- Combined score: `(raw_score * 0.6 + stance_value * 0.4) * max(confidence, 0.1)`
- Selects assets above threshold (-0.50)
- Persists `selection_run` with included/excluded assets and reasons

### Allocation
- Converts positive scores to raw weights
- Normalizes to 95% max invested (5% cash reserve)
- Caps individual positions at 15%
- Floors at 2% minimum per selected asset
- Persists `allocation_result` with method="score-weighted"

### Timing
- Classifies each asset: enter_now / stage_in / defer / reduce
- Based on confidence (≥0.6 = enter_now), risk level, stance
- Overall urgency: soon if majority are enter_now/stage_in, else wait
- Persists `timing_result` with urgency and horizon_days=90

### Risk Overlay
- Max position cap: 15%
- Confidence floor: halves weight if confidence < 20%
- High-risk trim: reduces by 30% for Elevated/High risk assets
- Ensures total ≤ 95%
- Computes portfolio_risk_score from average risk levels
- Persists `risk_overlay_result` with pre/post weights and adjustments

### Recommendation Generation
- Creates `Recommendation` with status="draft" (NOT published)
- Confidence triplet: model=avg engine confidence, data=0.90, operational=0.95 minus warnings
- Persists `recommendation_weights` with target/previous/delta/stance/rationale
- Attaches lineage: `source_feature_set_id`, `source_signal_run_ids`
- Creates audit event

---

## 5. Lineage

```
market_bars + news_events
    → feature_set (source_manifest_ids)
        → signal_runs (feature_set_id)
            → signal_outputs (signal_run_id → artifacts.source_feature_set_id)
                → recommendation (source_feature_set_id, source_signal_run_ids)
```

Every pipeline-generated recommendation is traceable back to the exact feature set and engine runs used.

---

## 6. Test Output

```
$ python -m pytest tests/ -v
108 passed, 1 warning in 5.86s

  11 new Phase 4D tests
  97 existing tests — all PASS (zero regressions)
```

### Seed Verification

```
$ rm -f finrlx_dev.db && alembic upgrade head && python -m seed
6 migrations OK
Pipeline completed: draft recommendation with 10 positions
```

---

## 7. What Is Now Real

| Layer | Status |
|---|---|
| Ingestion → DB | **REAL** (deterministic local adapter) |
| DB → Features | **REAL** (computed from market_bars + news_events) |
| Features → Signals | **REAL** (3 engines read feature_values) |
| Signals → Selection | **REAL** (aggregate scores from signal_outputs) |
| Selection → Allocation | **REAL** (score-weighted normalization with caps) |
| Allocation → Timing | **REAL** (confidence/risk-based classification) |
| Timing → Risk Overlay | **REAL** (position cap, confidence floor, risk trim) |
| Risk → Recommendation | **REAL** (draft rec with weights, lineage, confidence triplet) |

**Complete data flow:** `market_bars` → `feature_values` → `signal_outputs` → `selection` → `allocation` → `timing` → `risk_overlay` → `recommendation`

---

## 8. What Remains

| Component | Status |
|---|---|
| Market bar data source | Deterministic local adapter (not real market feeds) |
| Publication workflow | Recommendation created as "draft" — publication logic is Phase 4E |
| Frontend wiring | New pipeline endpoints not yet consumed by frontend |
| Old seeded recommendation | Still exists in DB alongside pipeline-generated ones |

---

## 9. Known Limitations

1. **Recommendation is draft, not published.** The overview/current endpoints still show the old seeded "published" recommendation. Publication workflow is Phase 4E scope.
2. **Data confidence is hardcoded at 0.90.** Should be derived from feature freshness in future.
3. **Selection threshold is generous (-0.50).** Tuning deferred to validation phase.
4. **Timing horizon is fixed at 90 days.** Not derived from signal metadata yet.
5. **No engine weighting.** All engines contribute equally (1/3 each).
6. **Pipeline doesn't prevent duplicate runs.** Each `POST /pipeline/run` creates a new recommendation.

---

## Phase 4D.1 Visibility & API Completion Addendum

**Date:** 2026-04-24

### Changes

1. **Pipeline runs list/detail added.**
   - `GET /pipeline/runs` — lists pipeline-generated recommendations with lineage, weight count, confidence
   - `GET /pipeline/runs/{id}` — full detail with selection, allocation, timing, risk_overlay stage records

2. **signal_run_ids now honored.** When `PipelineRunRequest.signal_run_ids` is provided, the pipeline validates they are registered + completed, rejects legacy/unknown runs, and derives the common feature_set_id.

3. **`/recommendations/current` now surfaces pipeline drafts truthfully.**
   - Published recommendation still takes priority
   - If no published exists but a pipeline draft does: returns the draft with warning "No published recommendation exists; returning latest pipeline-generated draft."
   - If published exists but a newer pipeline draft is behind it: adds warning "A newer pipeline-generated draft exists but is not published yet."

4. **`/overview` now warns about newer drafts.**
   - Same logic: if no published, shows draft as `current_recommendation` with warning
   - If published is older than latest draft: adds meta warning
   - Response shape preserved — frontend will not break

5. **Frontend impact:** The frontend will now see pipeline-generated data through existing `/recommendations/current` and `/overview` endpoints WITHOUT any frontend code changes. If the old seeded "published" recommendation exists, it still shows. If it doesn't (e.g., after an action changed its status), the pipeline draft surfaces automatically.

### Tests Added (5)

| Test | What It Verifies |
|---|---|
| `test_pipeline_runs_list` | GET /pipeline/runs returns pipeline recs with lineage |
| `test_pipeline_run_detail` | GET /pipeline/runs/{id} returns all stage records |
| `test_pipeline_run_detail_not_found` | GET /pipeline/runs/bad-id returns 404 |
| `test_current_shows_draft_when_no_published` | /current returns draft with appropriate warning |
| `test_overview_warns_about_newer_draft` | /overview preserves shape and warns about newer draft |

### Test Output

```
$ python -m pytest tests/ -v
113 passed, 1 warning in 5.80s

  16 Phase 4D tests (11 original + 5 visibility)
  97 existing tests — all PASS (zero regressions)
```

---

## 10. Recommended Phase 4E Prompt

```
You are continuing the FINRLX / QuantPipeline project.

Your task is Phase 4E: Publication Workflow.

Read the Phase 4D report at DOCS/handoff/PHASE_4D_DECISION_PIPELINE_REPORT.md first.
Read Doc 14 (Governance, Guardrails, Ops Reliability Specification).

Scope:
1. Create service: backend/app/services/publication.py with PublicationGate
   - evaluate_gates(recommendation_id) — check freshness, confidence, policy
   - publish(recommendation_id) — promote draft to published
   - suppress(recommendation_id, reason) — suppress with reason
2. Add endpoints: POST /api/v1/publication/{id}/publish, POST /suppress, GET /gates
3. Update overview/current endpoints to prefer pipeline-generated published recs
4. Write tests
5. Do NOT touch frontend
6. All existing 108 tests must still pass
```
