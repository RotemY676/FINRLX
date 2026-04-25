# Phase 6C: ML Shadow Backtest & Promotion Governance — Report

**Date:** 2026-04-25
**Phase:** 6C — Shadow backtest comparison + promotion review layer
**Status:** Complete

---

## 1. Files Changed

### Created (4)
```
backend/app/services/ml_promotion.py                — MLPromotionService
backend/app/api/v1/model_promotion.py               — 5 promotion endpoints
backend/migrations/versions/012_ml_promotion_reviews.py — ml_promotion_reviews table
backend/tests/test_phase6c_ml_shadow_promotion.py   — 12 promotion tests
DOCS/handoff/PHASE_6C_ML_SHADOW_BACKTEST_PROMOTION_REPORT.md
```

### Modified (7)
```
backend/app/models/modeling.py       — added MLPromotionReview model
backend/app/models/__init__.py       — registered MLPromotionReview
backend/app/schemas/modeling.py      — added promotion fields to ModelStatusResponse
backend/app/services/modeling.py     — get_status includes promotion review summary
backend/app/services/backtesting.py  — added include_shadow_engines parameter
backend/app/api/router.py           — registered model_promotion_router
```

---

## 2. Table Added (migration 012)

| Table | Key Columns |
|---|---|
| `ml_promotion_reviews` | id, model_key, model_version, reviewed_at, baseline_backtest_id, shadow_backtest_id, validation_report_id, baseline_metrics (JSON), shadow_metrics (JSON), metric_deltas (JSON), sample_count, recommendation, decision, warnings (JSON) |

**recommendation** = system-computed suggestion: `not_ready`, `needs_more_data`, `promising_shadow`, `eligible_for_review`, `reject`

**decision** = human/operator decision, default null. Accepted values: `keep_shadow`, `request_more_data`, `eligible_for_review`, `reject`

---

## 3. Endpoints Added (5)

| Method | Path | Purpose |
|---|---|---|
| POST | `/models/promotion/review` | Run baseline + shadow backtests and produce promotion review |
| GET | `/models/promotion/latest` | Latest promotion review |
| GET | `/models/promotion/history` | Promotion review history |
| GET | `/models/promotion/{review_id}` | Single promotion review detail |
| POST | `/models/promotion/{review_id}/decision` | Record operator decision (does NOT activate ML) |

### Modified Endpoint
| Method | Path | Change |
|---|---|---|
| GET | `/models/status` | Now includes `latest_promotion_review_id`, `promotion_review_recommendation`, `promotion_review_decision`, `shadow_backtest_delta_summary`, `still_shadow` |

---

## 4. Shadow Backtest Methodology

**Baseline backtest:**
- Runs `BacktestService.run_backtest()` with `include_shadow_engines=False` (default)
- Pipeline uses only deterministic engines: `technical_momentum`, `risk_quality`, `news_sentiment`
- ML engine signals are excluded from scoring

**Shadow backtest:**
- Runs `BacktestService.run_backtest()` with `include_shadow_engines=True`
- Pipeline includes `ml_return_forecaster` shadow engine in scoring
- Results labeled with `experimental_context="ml_shadow"`, `model_key="ml_return_forecaster"`
- Backtest recommendations tagged `context="backtest"` — excluded from `/recommendations/current` and `/overview`

**Both backtests:**
- Walk-forward simulation using real `market_bars` close prices
- Features computed as-of each rebalance date (no lookahead)
- Transaction cost applied at each rebalance
- Equity curve, drawdown, returns computed from actual prices

---

## 5. Comparison Formulas

For each metric, delta = shadow_value − baseline_value:

| Metric | Delta Key |
|---|---|
| Total return | `total_return_delta` |
| Annualized return | `annualized_return_delta` |
| Sharpe ratio | `sharpe_ratio_delta` |
| Max drawdown | `max_drawdown_delta` |
| Volatility | `volatility_delta` |
| Avg turnover | `avg_turnover_delta` / `turnover_delta` |
| Total trades | `total_trades_delta` / `trade_count_delta` |
| Win rate | `win_rate_delta` |
| Decision count | `decision_count_delta` |
| Directional accuracy | from latest validation report |
| Calibration error | from latest validation report |

---

## 6. Promotion Readiness Gates

| Gate | Rule | On Failure |
|---|---|---|
| Sample count | `sample_count >= 20` | `needs_more_data` |
| Validation readiness | `promotion_readiness != "not_ready"` | `not_ready` |
| Directional accuracy | `>= 0.52` | `not_ready` |
| Critical validation warnings | none present | `reject` |
| Shadow total return | `>= baseline` (warning if not, not auto-reject) | warning |
| Max drawdown | shadow not worse by > 5 percentage points | `reject` |
| Turnover ratio | shadow turnover `<= 2x` baseline (unless return improves) | `reject` |

**If sample_count < 20:** recommendation is always `needs_more_data`, regardless of other metrics.

**If all gates pass:**
- `directional_accuracy >= 0.58` → `eligible_for_review`
- `directional_accuracy >= 0.52` → `promising_shadow`

---

## 7. How Live Pipeline Remains Protected

1. **Default pipeline excludes ML.** `DecisionPipelineService._get_registered_signals()` filters `category != "ml"` by default.
2. **Backtest recs tagged.** All backtest recommendations get `context="backtest"` — filtered out of `/recommendations/current` and `/overview`.
3. **No automatic promotion.** The service never changes `ModelDefinition.status` or `is_shadow`.
4. **Operator decision is advisory.** `POST /promotion/{id}/decision` only records the operator's choice — it does not toggle any engine flag.
5. **Shadow backtests are separate experiments.** They create their own `BacktestExperiment` records and do not modify existing backtests.

---

## 8. Test Output

```
$ python -m pytest tests/ -v
207 passed, 2 skipped, 1 warning in 16.68s

  12 new Phase 6C tests
  195 existing tests — all PASS (zero regressions)
```

### Phase 6C Tests (12)

| Test | What It Verifies |
|---|---|
| `test_promotion_review_can_be_created` | POST /models/promotion/review creates a persisted review |
| `test_baseline_backtest_excludes_ml` | Baseline backtest config has include_shadow_engines=false |
| `test_shadow_backtest_includes_ml` | Shadow backtest config has include_shadow_engines=true |
| `test_live_recs_not_polluted_by_shadow_backtest` | /recommendations/current not affected by shadow backtests |
| `test_comparison_metrics_include_deltas` | Review includes return/sharpe/drawdown/turnover deltas |
| `test_sample_count_low_forces_needs_more_data` | sample_count < 20 → needs_more_data |
| `test_promotion_review_persisted` | Review queryable by ID and via /latest |
| `test_model_status_includes_promotion_review` | /models/status includes promotion review summary |
| `test_operator_decision_records_but_does_not_activate` | Decision records but ML stays shadow |
| `test_ml_remains_shadow_after_review` | ML model remains experimental/shadow |
| `test_promotion_history` | /models/promotion/history returns list |
| `test_invalid_decision_rejected` | Invalid decision value returns 400 |

---

## 9. What Is Now Real

| Component | Status |
|---|---|
| Promotion review table | **REAL** — persisted in `ml_promotion_reviews` |
| Shadow backtest comparison | **REAL** — runs actual backtests with/without ML |
| Metric deltas | **REAL** — computed from real backtest results |
| Promotion readiness gates | **REAL** — sample count, accuracy, drawdown, turnover checks |
| Operator decision recording | **REAL** — advisory decisions persisted |
| Model status with promotion info | **REAL** — includes latest review summary |

---

## 10. What Remains Experimental

- ML model `ml_return_forecaster` remains `status="experimental"`, `is_shadow=true`
- No automatic promotion — all promotion decisions are advisory
- No RL / FINRL-X implemented
- No broker/execution
- No publication governance bypass

---

## 11. Known Limitations

1. **Limited test data** — in test environment, sample_count < 20, so recommendation is always `needs_more_data`.
2. **Backtest cost** — each promotion review runs two full backtests (baseline + shadow), which is expensive.
3. **No benchmark comparison** — shadow vs baseline comparison is relative to each other, not to an external benchmark.
4. **No time-series comparison** — comparison is summary-level metrics only, not point-by-point equity curve comparison.
5. **Turnover ratio gate** — uses `avg_turnover` which may be None if backtests have < 2 rebalance periods.
6. **No model versioning** — single v1 model, no version-specific promotion review.
7. **Operator decisions are advisory only** — no workflow enforcement or approval chain.

---

## 12. Recommended Next Phase Prompt

```
Phase 7: [Future — RL / FINRL-X integration]
- Implement reinforcement learning policy optimization
- Model registry versioning workflow
- Promotion workflow with approval chain
- Live A/B testing framework for shadow vs production
```

**Do not start Phase 7 without explicit instruction.**
