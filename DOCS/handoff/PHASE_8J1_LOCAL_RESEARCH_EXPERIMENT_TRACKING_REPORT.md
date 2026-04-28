# Phase 8J.1 — Local Research Experiment Tracking Report

**Date:** 2026-04-28
**Accepted checkpoint:** Phase 8I.2-fix2 (commit aa8c020)
**Classification:** PASS

---

## 1. Executive Summary

Phase 8J.1 adds a controlled, local/offline experiment tracking layer that lets an operator register research experiments linked to governed dataset exports. The system is a research ledger — it tracks experiment metadata only. It does not run training, benchmarks, or affect production decisions in any way.

---

## 2. Files Changed

| File | Action |
|------|--------|
| `backend/app/api/v1/rl_finrlx.py` | Modified — added 7 experiment tracking endpoints |
| `backend/app/services/finrlx_research.py` | Modified — added experiment registry service methods |
| `backend/tests/test_phase8j1_experiment_tracking.py` | Created — 34 tests |
| `frontend/src/services/api.ts` | Modified — added experiment tracking types and API functions |
| `frontend/src/app/admin/page.tsx` | Modified — added Local Research Experiments UI section |
| `research/finrlx_cpu/experiments/.gitkeep` | Created — marker for experiments directory |
| `DOCS/handoff/PHASE_8J1_LOCAL_RESEARCH_EXPERIMENT_TRACKING_REPORT.md` | Created — this report |
| `DOCS/handoff/PHASE_8J1_LOCAL_VERIFICATION_EVIDENCE.txt` | Created — verification evidence |

---

## 3. Design Handoff Review

**Files inspected:**
- `design/handoff-package/HANDOFF.md` — full design system documentation
- `design/handoff-package/shell.jsx` — TopBar, LeftNav, Brand components
- `design/handoff-package/icons.jsx` — SVG icon set
- `design/handoff-package/Decision Workspace.html` — decision workspace surface

**UI conventions preserved:**
- Dark theme default with CSS custom properties (`--surface`, `--ink`, `--primary`, `--pos`, `--caution`, `--breach`)
- Card layout: `rounded-lg border border-line bg-surface p-pad shadow-sm`
- Label/input pattern: `text-[10px] text-ink-4` labels, `text-[11px]` inputs with `border-line bg-surface`
- Safety badges: `inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3`
- Acknowledgement pattern: checkbox + descriptive text in `bg-surface-2` container
- Error/success messages: `bg-breach/10 border-breach/20 text-breach` / `bg-pos/10 border-pos/20 text-pos`
- Monospace for IDs/hashes: `font-mono text-ink-2 break-all`
- Mobile safety: flex-wrap, truncate, max-w constraints, stacking on small screens

**No design files were modified.** The experiment tracking UI follows the exact same patterns as the Dataset Export and Dataset Export Governance sections.

---

## 4. Backend Experiment Registry Implementation

**Registry file:** `research/finrlx_cpu/experiments/experiment_registry.json`

**Service methods added to `FinRLXResearchService`:**
- `load_experiment_registry()` — loads from disk, creates if missing, marks corrupt if unreadable
- `save_experiment_registry()` — atomic write via temp file + replace
- `create_research_experiment()` — creates experiment linked to validated export
- `list_research_experiments()` — newest first, optional lifecycle filter
- `get_research_experiment()` — by ID with safety flags
- `update_research_experiment_state()` — tracking label change only
- `import_research_experiment_results()` — metadata-only, sanitized
- `verify_research_experiment()` — read-only, checks linked export health
- `rebuild_experiment_registry_from_files()` — creates fresh empty registry

**Safety properties:**
- All operations confined to `research/finrlx_cpu/experiments/`
- No absolute paths stored
- No secrets/env vars/credentials stored
- Corrupt registry detected and not silently overwritten
- Result import sanitizes to primitive types only (int, float, str)
- Verify is strictly read-only — no registry writes

---

## 5. Backend API Changes

**Endpoints added:**

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/rl/finrlx/research-experiments` | Create experiment |
| GET | `/api/v1/rl/finrlx/research-experiments` | List experiments |
| GET | `/api/v1/rl/finrlx/research-experiments/{id}` | Get experiment |
| POST | `/api/v1/rl/finrlx/research-experiments/{id}/state` | Update lifecycle state |
| POST | `/api/v1/rl/finrlx/research-experiments/{id}/results` | Import result metadata |
| GET | `/api/v1/rl/finrlx/research-experiments/{id}/verify` | Verify linked export |
| POST | `/api/v1/rl/finrlx/research-experiments/rebuild-registry` | Rebuild registry |

All endpoints require explicit acknowledgement for write operations.

---

## 6. Frontend/Admin UI Changes

**New section:** "Local Research Experiments" in Admin page, positioned after Dataset Export Governance and before Run Offline Benchmark.

**UI features:**
1. Create experiment form with name, linked export ID, hypothesis, method notes, parameters JSON, expected metrics, and research acknowledgement
2. Experiment list with ID, name, linked export, lifecycle state badge, result status, creation date
3. Experiment detail panel with full metadata, linked export checksum/fingerprint, safety flags
4. Lifecycle state controls with dropdown, reason field, and acknowledgement
5. Metadata-only result import with summary text and metrics JSON
6. Verify linked export button (read-only)
7. Rebuild experiment registry control

**Safety badges:** research-only, offline-only, not eligible for promotion

**Mobile/tablet safety:** flex-wrap, truncate on long IDs, max-w constraints, stacking controls

---

## 7. Experiment Registry Schema

```json
{
  "version": 1,
  "updated_at": "ISO timestamp",
  "experiments": [
    {
      "experiment_id": "uuid",
      "created_at": "ISO timestamp",
      "updated_at": "ISO timestamp",
      "lifecycle_state": "planned|running_offline|completed|failed|archived",
      "name": "string",
      "linked_export_id": "uuid",
      "linked_export_fingerprint": "hex16",
      "linked_export_checksum": "hex32",
      "linked_export_row_count": 0,
      "linked_export_date_range": {"start": "date", "end": "date"},
      "hypothesis": "string",
      "method_notes": "string",
      "parameters": {},
      "expected_metrics": [],
      "result_summary": null,
      "result_metrics": {},
      "result_artifact_path": null,
      "warnings": [],
      "limitations": [],
      "research_only": true,
      "offline_only": true,
      "shadow_only": true,
      "no_production_influence": true,
      "not_eligible_for_promotion": true
    }
  ]
}
```

---

## 8. Linked Dataset Export Model

- Creating an experiment requires a valid `linked_export_id` that exists in the dataset export registry
- Export checksum, fingerprint, row count, and date range are captured at experiment creation
- Verify checks if linked export is still present, active, and has matching checksum
- Stale/missing exports produce warnings, not errors

---

## 9. Result Metadata Import Model

- Metadata-only: text summaries and numeric/string metric values
- No executable code, no file uploads, no arbitrary filesystem paths
- Result metrics sanitized to primitive types (int, float, str)
- Non-primitive nested values are silently dropped
- String values truncated to 500 chars, summaries to 2000 chars

---

## 10. Path Safety Model

- All registry operations confined to `research/finrlx_cpu/experiments/`
- No absolute filesystem paths stored in registry
- No secrets, env vars, API keys, or credentials stored
- API-returned paths are relative safe paths

---

## 11. Read-Only Verification Model

- `verify_research_experiment()` reads registry and export registry but never writes
- Registry file content unchanged after verify calls (proven by test)
- Missing/stale/corrupt linked exports produce warnings, not fabricated data

---

## 12. Lifecycle Model

**Allowed states:** planned, running_offline, completed, failed, archived

**Important:**
- Lifecycle state is a tracking label only
- `running_offline` does not trigger execution
- `completed` does not make results production-eligible
- No lifecycle state influences recommendations, overview, publication, candidate status, or promotion

---

## 13. Operator Controls

- Create experiment: requires research acknowledgement
- Update state: requires acknowledgement
- Import results: requires acknowledgement, metadata-only
- Verify: read-only, no acknowledgement needed
- Rebuild registry: requires acknowledgement

---

## 14. Safety and Isolation Analysis

| Property | Status |
|----------|--------|
| Research-only | Enforced |
| Offline-only | Enforced |
| Shadow-only | Enforced |
| No production influence | Enforced |
| Not eligible for promotion | Enforced |
| No broker execution | Enforced |
| No automatic training | Enforced |
| No automatic benchmark execution | Enforced |
| No recommendation pollution | Enforced |
| No overview influence | Enforced |
| No publication influence | Enforced |
| No model promotion | Enforced |
| `/rl/execute` absent | Confirmed (404) |

---

## 15. Tests Added

**File:** `backend/tests/test_phase8j1_experiment_tracking.py` — 34 tests

1. Experiment registry created when missing
2. Create requires acknowledgement
3. Create requires valid linked export
4. Create succeeds with valid export
5. Created experiment includes safety flags
6. Created experiment stores linked export metadata
7. Registry paths relative
8. Registry never stores absolute paths
9. Registry never stores secrets
10. List experiments newest first
11. Get experiment by ID returns full schema
12. Invalid experiment ID returns 404
13. Lifecycle update requires acknowledgement
14. Lifecycle update rejects invalid state
15. Lifecycle update succeeds
16. Result import requires acknowledgement
17. Result import is metadata-only
18. Result import sanitizes unsafe fields
19. Verify is read-only (no registry modification)
20. Verify reports stale linked export
21. Corrupt registry not silently overwritten
22. Corrupt registry returns safe warning
23. Rebuild requires acknowledgement
24. Rebuild succeeds
25. Does not alter recommendations
26. Does not alter overview
27. Does not alter publication
28. Does not promote candidates
29. Does not trigger training
30. Does not trigger benchmark
31. `/rl/execute` remains absent
32. Phase 8I exports still work
33. Phase 8A status still works
34. Existing pipeline still works

---

## 16. Tests Run and Results

**Phase 8J.1 targeted tests:** 34 passed, 0 failed
**Phase 8I + 8I.2 + 8J.1 targeted tests:** 89 passed, 0 failed
**Full Phase 8 regression (8A, 8B, 8E, 8F, 8I, 8I.2, 8J.1):** 175 passed, 0 failed

---

## 17. Frontend Build/Typecheck/Lint Results

- `npm run build`: SUCCESS (all routes compiled, /admin 20.4 kB)
- `npm run typecheck`: SUCCESS (no errors)
- `npm run lint`: SUCCESS (no warnings or errors)

---

## 18. Unsafe Language Grep Result

Searched: `frontend/src/app/admin/page.tsx`, `frontend/src/services/api.ts`, `backend/app/api/v1/rl_finrlx.py`, `backend/app/services/finrlx_research.py`
Patterns: buy, sell, trade now, execute trade, live signal, best investment, production alpha, deploy policy

**Result:** No matches found.

---

## 19. Production/Container Persistence Note

The experiment registry (`research/finrlx_cpu/experiments/experiment_registry.json`) is stored on the local filesystem. In container/Railway deployments, this data may be ephemeral unless a persistent volume or external storage is configured. This is by design for the research-only workflow — production decisions do not depend on experiment registry data.

---

## 20. Known Limitations

1. Experiment registry is file-backed (ephemeral in container deployments without persistent storage)
2. No concurrent-write protection beyond atomic file replace
3. Experiment metadata is stored in a flat JSON array (suitable for research-scale, not production-scale)
4. Result metrics are sanitized to primitives — complex nested structures are dropped
5. Rebuild registry creates an empty registry (experiments are metadata-only with no filesystem artifacts to scan)
6. No experiment versioning or diff tracking

---

## 21. Stop/Go Recommendation

**GO** — Phase 8J.1 is complete and verified.

All backend tests pass (175/175 Phase 8 regression). Frontend builds, typechecks, and lints cleanly. No unsafe language detected. Safety flags enforced on all experiment operations. Production isolation confirmed via dedicated tests.
