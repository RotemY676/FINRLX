# Phase 6A: Model Registry & ML Engine Prep — Report

**Date:** 2026-04-25
**Phase:** 6A — ML model registry + baseline ML engine
**Status:** Complete

---

## 1. Files Changed

### Created (6)
```
backend/app/models/modeling.py              — ModelDefinition, ModelRun, ModelPrediction
backend/app/schemas/modeling.py             — 6 ML schemas
backend/app/services/modeling.py            — ModelingService + baseline linear predictor
backend/app/api/v1/models.py                — 6 ML API endpoints
backend/migrations/versions/010_model_registry.py — 3 new tables
backend/tests/test_phase6a_model_registry_ml.py  — 10 ML tests
DOCS/handoff/PHASE_6A_MODEL_REGISTRY_ML_PREP_REPORT.md
```

### Modified (5)
```
backend/app/models/__init__.py     — registered ML models
backend/app/schemas/__init__.py    — registered ML schemas
backend/app/api/router.py          — registered models_router
backend/app/services/engines.py    — added ml_return_forecaster engine + _run_ml_engine method
backend/seed.py                    — ensure ML model definition
backend/tests/test_phase4c_engines.py — updated for 4 engines (was 3)
```

---

## 2. Tables Added (migration 010)

| Table | Key Columns |
|---|---|
| `model_definitions` | key, name, category, model_type, target, feature_keys, status, is_shadow |
| `model_runs` | model_key, run_type (train/predict), status, metrics, source_feature_set_ids |
| `model_predictions` | model_run_id, asset_id, ticker, prediction_value, prediction_score, confidence, quality |

---

## 3. Baseline ML Model

**Key:** `ml_return_forecaster`
**Type:** `baseline_linear` — NOT advanced ML
**Target:** `forward_return_20d`
**Status:** `experimental`, `is_shadow=true`

**Methodology:**
```
For each feature_key with quality=ok:
  norm = feature_value / scale_factor
  contribution = baseline_weight × norm

score = sum(contributions)  clamp to [-1, 1]
predicted_return = score × 0.10  (±10% expected return)
confidence = 0.15 + (ok_features / total_features) × 0.60
quality = "ok" if ≥4 features, "partial" if ≥2, "insufficient_data" otherwise
```

**Baseline weights (fixed, not learned):**
- return_5d: +0.10, return_20d: +0.25, return_60d: +0.20
- volatility_20d: -0.15, drawdown_20d: +0.10
- relative_volume_20d: +0.05
- news_sentiment_7d: +0.10, news_count_7d: +0.05

**No external dependencies.** No scikit-learn, no numpy, no network calls.

---

## 4. ML Engine Integration

The `ml_return_forecaster` engine reads from `model_predictions` (not feature_values directly).

Flow: `features → ModelingService.predict() → model_predictions → EngineService._run_ml_engine() → signal_outputs`

- If no model predictions exist, produces a single hold signal with confidence 0.05 and caveat
- ML signals are labeled `"ML baseline / experimental / shadow"` in caveats
- ML engine is one of 4 active engines but doesn't dominate allocation (equal weight 1/4)

---

## 5. Endpoints Added (6)

| Method | Path | Purpose |
|---|---|---|
| GET | `/models/definitions` | List model definitions |
| GET | `/models/status` | Model registry status |
| POST | `/models/train` | Train baseline model (records context) |
| POST | `/models/predict` | Generate predictions from features |
| GET | `/models/runs` | List model runs |
| GET | `/models/predictions` | Latest predictions |

---

## 6. Test Output

```
181 passed, 2 skipped, 1 warning in 14.09s

  10 new Phase 6A tests
  171 existing tests — all PASS
```

---

## 7. What Is Now Real

| Component | Status |
|---|---|
| Model registry | **REAL** — definitions, runs, predictions persisted |
| Baseline predictions | **REAL** — computed from feature_values |
| ML engine signals | **REAL** — reads model_predictions, writes signal_outputs |
| Lineage | **REAL** — model_run → feature_set → signal_output |

---

## 8. What Is Baseline/Experimental

- Model is `baseline_linear` with fixed manually-calibrated weights — NOT learned from data
- Training is a no-op for the model itself (only records context/metrics)
- Labeled `experimental` and `is_shadow=true`
- No RL, no deep learning, no external ML frameworks

---

## 9. Known Limitations

1. **No real ML training** — weights are fixed, not optimized from data.
2. **No scikit-learn** — lightweight manual implementation only.
3. **ML is shadow** — included in engine runs but marked experimental.
4. **No model versioning workflow** — single v1 only.
5. **No model promotion gates** — no validation-before-production lifecycle yet.
6. **No RL/FINRL-X** — deferred to future phase.

---

## Phase 6A.1 Shadow ML Isolation Addendum

**Date:** 2026-04-25

### Changes

1. **Pipeline excludes shadow/ML by default.** `_get_registered_signals` now filters to `category != "ml"` engines unless `include_shadow_engines=True` is passed.

2. **Opt-in flag.** `PipelineRunRequest.include_shadow_engines` (default `false`). When true, ML signals are included and a warning is added: "Shadow/experimental ML signals included in this pipeline run."

3. **ML signals still generated.** `POST /engines/run` still produces `ml_return_forecaster` signal outputs for comparison/monitoring. They just don't feed into live pipeline scoring by default.

### Tests Added (3)

| Test | What It Verifies |
|---|---|
| `test_default_pipeline_excludes_ml` | Default pipeline has no shadow warning |
| `test_pipeline_with_shadow_includes_ml` | include_shadow=true produces shadow warning |
| `test_ml_signals_still_generated` | ML engine still creates signal_outputs |

### Test Output

```
184 passed, 2 skipped, 1 warning in 14.44s
```
