# Phase 6D: ML Observability & Ops Integration — Report

**Date:** 2026-04-25
**Phase:** 6D — ML ops summary, warnings, governance posture, admin UI
**Status:** Complete

---

## 1. Files Changed

### Created (4)
```
backend/app/services/ml_ops.py                     — MLOpsService
backend/app/schemas/ml_ops.py                      — 7 ML ops schemas
backend/app/api/v1/ml_ops.py                       — 4 ML ops endpoints
backend/tests/test_phase6d_ml_ops_observability.py  — 13 ML ops tests
DOCS/handoff/PHASE_6D_ML_OBSERVABILITY_OPS_REPORT.md
```

### Modified (4)
```
backend/app/api/router.py           — registered ml_ops_router
backend/app/api/v1/ops.py           — added ml_ops block to /ops response
backend/app/schemas/ops.py          — added OpsMLBlock, ml_ops field to OpsCommandCenterResponse
frontend/src/services/api.ts        — added OpsMLBlock, MLOpsSummary types + fetchMLOpsSummary()
frontend/src/app/admin/page.tsx     — added ML Observability card
```

---

## 2. Endpoints Added (4)

| Method | Path | Purpose |
|---|---|---|
| GET | `/ml-ops/summary` | Full ML ops summary (model, validation, promotion, shadow, warnings, action) |
| GET | `/ml-ops/models/{model_key}` | Combined health/validation/promotion/shadow detail for one model |
| GET | `/ml-ops/models/{model_key}/warnings` | Structured warnings list for a model |
| GET | `/ml-ops/models/{model_key}/shadow-status` | Shadow status and pipeline influence |

### Modified Endpoint
| Method | Path | Change |
|---|---|---|
| GET | `/ops` | Now includes `ml_ops` block with model counts, shadow status, validation, warnings |

---

## 3. ML Ops Summary Design

The `GET /ml-ops/summary` endpoint returns a single consolidated view:

| Field | Source |
|---|---|
| `model_key`, `model_name`, `status`, `is_shadow` | `model_definitions` table |
| `latest_prediction_run_id`, `latest_prediction_status`, `prediction_count` | `model_runs` + `model_predictions` |
| `latest_validation_report_id`, `validation_status`, `validation_sample_count` | `model_validation_reports` |
| `directional_accuracy`, `calibration_error`, `promotion_readiness` | `model_validation_reports` |
| `latest_promotion_review_id`, `promotion_review_recommendation`, `promotion_review_decision` | `ml_promotion_reviews` |
| `baseline_total_return`, `shadow_total_return`, `total_return_delta` | `ml_promotion_reviews.baseline_metrics/shadow_metrics` |
| `max_drawdown_delta`, `sharpe_delta` | `ml_promotion_reviews.metric_deltas` |
| `still_shadow` | Always `true` |
| `live_pipeline_influence` | Always `false` |
| `warnings` | Aggregated from validation + promotion reviews |
| `recommended_operator_action` | Computed from current state |

### Recommended Operator Actions

| Action | When |
|---|---|
| `run_predictions` | No prediction run exists |
| `run_validation` | Predictions exist but no validation |
| `run_promotion_review` | Validation exists but no promotion review |
| `needs_more_data` | Sample count < 20 |
| `keep_shadow` | Promising but not ready for promotion |
| `eligible_for_manual_review` | All gates pass, accuracy >= 58% |
| `investigate_model` | Validation not_ready or promotion rejected |

---

## 4. /ops ML Block

The existing `GET /ops` response now includes:

```json
{
  "ml_ops": {
    "total_models": 1,
    "active_models": 1,
    "shadow_models": 1,
    "latest_validation_status": "completed",
    "promotion_readiness": "needs_more_data",
    "warning_count": 2,
    "any_model_influences_live_pipeline": false,
    "ml_is_shadow_only": true
  }
}
```

This makes it obvious that ML is shadow-only and does not influence the live pipeline.

---

## 5. Frontend Changes

### Admin/Ops Page — ML Observability Card

Added a compact card after the KPI strip showing:
- **Model**: `ml_return_forecaster`
- **Status**: `experimental` (amber badge)
- **Mode**: Shadow badge
- **Live influence**: Off badge
- **Predictions**: count
- **Validation**: status
- **Accuracy**: percentage with sample size
- **Readiness**: color-coded (green for eligible, amber for promising, grey for needs_more_data)
- **Baseline vs Shadow**: return delta, Sharpe delta, drawdown delta
- **Warnings**: structured list with icons
- **Recommended action**: human-readable suggestion

No navigation changes. No redesign. Consistent with existing Admin/Ops UI.

---

## 6. Test Output

### Backend
```
$ python -m pytest tests/ -v
220 passed, 2 skipped, 1 warning in 16.36s

  13 new Phase 6D tests
  207 existing tests — all PASS (zero regressions)
```

### Frontend
```
$ npm run build
✓ Compiled successfully
✓ Generating static pages (11/11)

Route (app)                              Size     First Load JS
├ ○ /admin                               5.87 kB          96 kB
... all pages compiled successfully
```

### Phase 6D Tests (13)

| Test | What It Verifies |
|---|---|
| `test_ml_ops_summary_works` | GET /ml-ops/summary returns valid response |
| `test_summary_includes_latest_model_run` | Summary has prediction run after predictions |
| `test_summary_includes_latest_validation` | Summary has validation report |
| `test_summary_includes_latest_promotion_review` | Summary has promotion review if exists |
| `test_summary_still_shadow_true` | still_shadow=true always |
| `test_summary_live_pipeline_influence_false` | live_pipeline_influence=false always |
| `test_warnings_include_sample_count` | Warnings include sample_count < 20 |
| `test_recommended_action_reasonable` | Action is one of expected values |
| `test_ops_includes_ml_block` | /ops includes ml_ops block with shadow flags |
| `test_pipeline_unchanged` | Deterministic pipeline still works |
| `test_ml_excluded_from_live_pipeline` | ML model remains shadow/experimental |
| `test_model_detail_endpoint` | /ml-ops/models/{key} returns combined detail |
| `test_warnings_endpoint` | /ml-ops/models/{key}/warnings returns list |

---

## 7. What Is Now Visible to Operators

| Component | Visibility |
|---|---|
| ML model status | **Visible** — via /ml-ops/summary and admin page |
| Prediction count | **Visible** — how many predictions exist |
| Validation metrics | **Visible** — accuracy, sample count, readiness |
| Promotion review | **Visible** — recommendation, decision, deltas |
| Shadow status | **Visible** — clearly marked shadow-only |
| Pipeline influence | **Visible** — clearly marked as Off |
| Warnings | **Visible** — structured list with levels |
| Recommended action | **Visible** — actionable suggestion |

---

## 8. What Remains Shadow/Experimental

- ML model `ml_return_forecaster` remains `status="experimental"`, `is_shadow=true`
- `live_pipeline_influence` is always `false`
- `still_shadow` is always `true`
- No automatic promotion
- No RL / FINRL-X implemented
- No broker/execution
- No governance bypass

---

## 9. Known Limitations

1. **Single model only** — summary is hardcoded to `ml_return_forecaster`. Multi-model support would need parameterization.
2. **No trend data** — summary shows current state only, not historical trends.
3. **No alerting** — warnings are passive, no push notifications or thresholds.
4. **Recommended action is advisory** — no one-click execution from the admin UI.
5. **Frontend card is read-only** — no interactive controls to run predictions/validation from the card.
6. **Warning deduplication** — some warnings may appear from both validation and promotion sources.

---

## 10. Recommended Next Phase Prompt

```
Phase 7: [Future — RL / FINRL-X integration]
- Implement reinforcement learning policy optimization
- Model versioning and A/B testing
- Promotion workflow with multi-step approval chain
- Live shadow → production switchover mechanism
- ML alerting and anomaly detection
```

**Do not start Phase 7 without explicit instruction.**
