# Phase 6B: ML Validation & Shadow Evaluation — Report

**Date:** 2026-04-25
**Phase:** 6B — Shadow ML evaluation against realized returns
**Status:** Complete

---

## 1. Files Changed

### Created (4)
```
backend/app/services/ml_validation.py            — MLValidationService
backend/app/api/v1/model_validation.py            — 4 validation endpoints
backend/migrations/versions/011_model_validation.py — model_validation_reports table
backend/tests/test_phase6b_ml_validation.py       — 11 validation tests
DOCS/handoff/PHASE_6B_ML_VALIDATION_SHADOW_EVALUATION_REPORT.md
```

### Modified (4)
```
backend/app/models/modeling.py     — added ModelValidationReport
backend/app/models/__init__.py     — registered ModelValidationReport
backend/app/schemas/modeling.py    — added validation fields to ModelStatusResponse
backend/app/services/modeling.py   — get_status includes latest validation summary
backend/app/api/router.py          — registered model_validation_router
```

---

## 2. Validation Methodology

For each `model_prediction`:
1. Find realized forward return from `market_bars` over `prediction_horizon_days`
2. Compare predicted vs realized direction

**Metrics:**
- `directional_accuracy` = correct_direction_count / total_evaluated
- `mean_absolute_error` = mean(|predicted - realized|)
- `rank_correlation` = Pearson correlation between predicted and realized values
- `hit_rate` = same as directional_accuracy (v1)
- `calibration_error` = avg |bucket_accuracy - expected_accuracy| across confidence buckets

**Confidence buckets:** low (<0.3), medium (0.3-0.6), high (>0.6)

**Baseline comparison:** Each deterministic engine's stance direction accuracy vs same realized returns.

---

## 3. Promotion Readiness Rules

| Readiness | Criteria |
|---|---|
| `not_ready` | directional_accuracy < 52% |
| `needs_more_data` | sample_count < 20 |
| `promising_shadow` | accuracy 52-58%, enough samples |
| `eligible_for_review` | accuracy ≥ 58%, enough samples |

**No automatic promotion.** ML remains shadow regardless of validation results.

---

## 4. Test Output

```
195 passed, 2 skipped, 1 warning in 16.54s

  11 new Phase 6B tests
  184 existing tests — all PASS
```

---

## 5. Known Limitations

1. **Limited realized return data** — deterministic local adapter provides ~90 days of bars, so forward 20-day returns may have very few evaluable samples.
2. **Rank correlation** uses Pearson on values (not true Spearman rank correlation).
3. **Calibration error** uses simple bucket comparison with hard-coded expected accuracies.
4. **No auto-promotion** — validation reports inform human review only.
5. **ML remains experimental/shadow** — not promoted regardless of validation outcome.
