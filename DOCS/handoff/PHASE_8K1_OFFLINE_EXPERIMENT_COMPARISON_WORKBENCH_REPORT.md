# Phase 8K.1 — Offline Experiment Comparison Workbench Report

**Date:** 2026-04-28
**Accepted checkpoint:** Phase 8J.1-fix2 (commit 90bb22d)
**Fix applied:** 8K.1-fix — defensive snapshot and summary sanitization
**Classification:** PASS

---

## 1. Executive Summary

Phase 8K.1 adds a controlled, local/offline experiment comparison workbench that lets an operator compare already-tracked research experiments using imported result metadata only. The system is a comparison aid and research ledger — it does not run training, benchmarks, inference, or affect production decisions.

---

## 2. Files Changed

| File | Action |
|------|--------|
| `backend/app/api/v1/rl_finrlx.py` | Modified — added 6 comparison endpoints |
| `backend/app/services/finrlx_research.py` | Modified — added comparison registry + comparison logic |
| `backend/tests/test_phase8k1_experiment_comparison.py` | Created — 38 tests |
| `frontend/src/services/api.ts` | Modified — added comparison types and API functions |
| `frontend/src/app/admin/page.tsx` | Modified — added Comparison Workbench UI section |
| `research/finrlx_cpu/comparisons/.gitkeep` | Created — marker for comparisons directory |

---

## 3. Design Handoff Review

**Files inspected:**
- `design/handoff-package/HANDOFF.md` — full design system documentation
- `design/handoff-package/shell.jsx` — TopBar, LeftNav, Brand components
- `design/handoff-package/icons.jsx` — SVG icon set
- `design/handoff-package/Decision Workspace.html` — decision workspace surface

**UI conventions preserved:**
- Dark theme default with CSS custom properties
- Card layout: `rounded-lg border border-line bg-surface p-pad shadow-sm`
- Safety badges: `inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3`
- Acknowledgement pattern: checkbox + descriptive text in `bg-surface-2` container
- Monospace for IDs: `font-mono text-ink-2 break-all`
- Mobile safety: flex-wrap, truncate, max-w constraints

**No design files were modified.**

---

## 4. Backend Comparison Registry Implementation

**Registry file:** `research/finrlx_cpu/comparisons/comparison_registry.json`

**Service methods added:**
- `load_comparison_registry()` — loads from disk, creates if missing, marks corrupt if unreadable
- `save_comparison_registry()` — atomic write via temp file + replace
- `create_experiment_comparison()` — creates comparison from 2+ experiments
- `list_experiment_comparisons()` — newest first, optional lifecycle filter
- `get_experiment_comparison()` — by ID with safety flags
- `archive_experiment_comparison()` — lifecycle change only, sanitized reason
- `verify_experiment_comparison()` — read-only, checks experiment references
- `rebuild_comparison_registry_from_files()` — creates fresh empty registry
- `_build_comparison_summary()` — deterministic metric comparison, no ML

---

## 5. Backend API Changes

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/rl/finrlx/experiment-comparisons` | Create comparison |
| GET | `/api/v1/rl/finrlx/experiment-comparisons` | List comparisons |
| GET | `/api/v1/rl/finrlx/experiment-comparisons/{id}` | Get comparison |
| POST | `/api/v1/rl/finrlx/experiment-comparisons/{id}/archive` | Archive comparison |
| GET | `/api/v1/rl/finrlx/experiment-comparisons/{id}/verify` | Verify comparison |
| POST | `/api/v1/rl/finrlx/experiment-comparisons/rebuild-registry` | Rebuild registry |

---

## 6. Frontend/Admin UI Changes

**New section:** "Offline Experiment Comparison Workbench" in Admin page, positioned after Local Research Experiments and before Run Offline Benchmark.

**Features:** Create form (name, experiment IDs, metric priority, notes, acknowledgement), comparison list, detail panel with experiment snapshots, ranked numeric metrics table, metric coverage, warnings, safety flags, verify button, archive controls.

---

## 7. Comparison Registry Schema

```json
{
  "version": 1,
  "updated_at": "ISO timestamp",
  "comparisons": [{
    "comparison_id": "uuid",
    "created_at": "ISO",
    "updated_at": "ISO",
    "lifecycle_state": "active|archived",
    "name": "string",
    "experiment_ids": ["uuid", "uuid"],
    "metric_priority": ["sharpe_ratio"],
    "notes": "string",
    "comparison_summary": { ... },
    "experiment_snapshots": [ ... ],
    "warnings": [],
    "limitations": [],
    "research_only": true,
    "offline_only": true,
    "shadow_only": true,
    "no_production_influence": true,
    "not_eligible_for_promotion": true
  }]
}
```

---

## 8. Experiment Snapshot Model

Each comparison snapshots experiment metadata at creation time: experiment_id, name, lifecycle_state, linked_export_id, linked_export_checksum, linked_export_fingerprint, linked_export_row_count, result_summary, result_metrics, warnings, limitations. Snapshots do not mutate experiments.

---

## 9. Metric Comparison Model

Deterministic comparison using only imported result_metrics. No ML, no inference, no benchmark execution.

- `metric_names`: union of all metric keys across experiments + metric_priority
- `ranked_metrics`: for each numeric metric, descending sorted list of {experiment_id, value}
- Limitation: "Metric sorting is numeric-only and does not imply production suitability."

---

## 10. Metric Coverage and Missing Metric Model

- `metric_coverage`: per metric — available_count, missing_count, coverage_ratio
- `missing_metrics`: per experiment — list of metric names missing from that experiment
- Warnings for: no result metrics, lifecycle not completed, mixed types, no comparable metrics

---

## 11. Path Safety Model

All registry operations confined to `research/finrlx_cpu/comparisons/`. No absolute paths, secrets, env vars stored. Reuses Phase 8J.1 sanitizer.

---

## 12. Sanitization Model

Reuses `_sanitize_experiment_text()`, `_sanitize_experiment_list()`, `_sanitize_experiment_dict()`, `_sanitize_experiment_metric_key()` from Phase 8J.1. Applied to:
- Comparison name, notes, metric_priority, archive reason
- **Experiment snapshot fields**: name, result_summary, result_metrics (keys+values), warnings, limitations
- **Comparison summary inputs**: metric_names filtered through `_sanitize_experiment_metric_key()`, metric warnings only include safe metric names
- Legacy/manual unsafe experiment metadata cannot leak into comparison_registry.json

---

## 13. Read-Only Verification Model

`verify_experiment_comparison()` reads registries but never writes. Registry content unchanged after verify (proven by test).

---

## 14. Lifecycle/Archive Model

Two states: active, archived. Archive is a lifecycle label change only — does not delete data, does not affect experiments, exports, recommendations, or production state. Archive reason is sanitized.

---

## 15. Operator Controls

- Create: requires research acknowledgement, min 2 experiments
- Archive: requires acknowledgement, sanitized reason
- Verify: read-only, no acknowledgement needed
- Rebuild: requires acknowledgement

---

## 16. Safety and Isolation Analysis

| Property | Status |
|----------|--------|
| Research-only | Enforced |
| Offline-only | Enforced |
| Shadow-only | Enforced |
| No production influence | Enforced |
| Not eligible for promotion | Enforced |
| No broker execution | Enforced |
| No training triggered | Enforced |
| No benchmark triggered | Enforced |
| No recommendation influence | Enforced |
| No overview influence | Enforced |
| No publication influence | Enforced |
| `/rl/execute` absent | Confirmed (404) |

---

## 17. Tests Added

**File:** `backend/tests/test_phase8k1_experiment_comparison.py` — 41 tests

Covering: registry creation, acknowledgement, min 2 IDs, valid IDs, success, safety flags, snapshots, linked export in snapshots, path safety, no absolute paths, no secrets, sanitization, list newest first, get by ID, invalid ID 404, archive acknowledgement, archive lifecycle, verify read-only, verify missing experiment, verify no result metrics, metric coverage, missing metrics per experiment, ranked metrics deterministic, mixed type warnings, no training, no benchmark, no altered recommendations, no altered overview, no altered publication, no promotion, corrupt comparison registry, corrupt experiment registry, rebuild acknowledgement, rebuild success, /rl/execute absent, Phase 8J.1 regression, pipeline regression.

---

## 18. Tests Run and Results

- Phase 8K.1 targeted: **41 passed**
- Phase 8I + 8I.2 + 8J.1 + 8K.1 targeted: **133 passed**
- Full Phase 8 regression: **219 passed**

---

## 19. Frontend Build/Typecheck/Lint Results

- Build: SUCCESS (/admin: 21.7 kB)
- Typecheck: SUCCESS (no errors)
- Lint: SUCCESS (no warnings)

---

## 20. Unsafe Language Grep Result

No matches for: buy, sell, trade now, execute trade, live signal, best investment, production alpha, deploy policy.

---

## 21. Production/Container Persistence Note

The comparison registry (`research/finrlx_cpu/comparisons/comparison_registry.json`) is stored on the local filesystem. In container/Railway deployments, this data may be ephemeral unless persistent storage is configured. Production decisions do not depend on comparison registry data.

---

## 22. Known Limitations

1. File-backed registry (ephemeral in container deployments)
2. No concurrent-write protection beyond atomic file replace
3. Flat JSON array (research-scale)
4. Ranked metrics use simple descending numeric sort — does not determine which direction is "better"
5. Rebuild creates empty registry (no filesystem artifacts to scan)
6. Comparison is a static snapshot — does not auto-update when experiments change

---

## 23. Stop/Go Recommendation

**GO** — Phase 8K.1 is complete and verified. All 216 Phase 8 regression tests pass. Frontend builds, typechecks, and lints cleanly. No unsafe language detected.
