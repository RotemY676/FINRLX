# Phase 8I.2: Dataset Export Governance, Persistence & Operator Controls

**Date:** 2026-04-27
**Phase:** 8I.2
**Status:** PASS

---

## 1. Executive Summary

Phase 8I.2 hardens the dataset export system with a persistent local export registry,
artifact health verification, lifecycle management (mark stale), and registry rebuild
from files. All governance endpoints remain research-only, offline-only, shadow-only
with no production influence.

---

## 2. Files Changed

| File | Change Type |
|------|------------|
| `backend/app/api/v1/rl_finrlx.py` | Modified — 3 governance endpoints + request models |
| `backend/app/services/finrlx_research.py` | Modified — registry system (load/save/register/list/get/mark-stale/verify/rebuild) |
| `backend/tests/test_phase8i_dataset_export.py` | Modified — updated list assertion for registry schema |
| `backend/tests/test_phase8i2_dataset_export_governance.py` | New — 24 governance tests |
| `frontend/src/services/api.ts` | Modified — governance types + 3 new API functions |
| `frontend/src/app/admin/page.tsx` | Modified — governance UI (registry list, detail panel, operator controls) |
| `DOCS/handoff/PHASE_8I2_DATASET_EXPORT_GOVERNANCE_REPORT.md` | New — this report |

---

## 3. Design Handoff Review

**Files inspected:**
- `design/handoff-package/HANDOFF.md`
- `design/handoff-package/shell.jsx`
- `design/handoff-package/icons.jsx`
- `design/handoff-package/Decision Workspace.html`

**UI conventions preserved:**
- Card sections: `rounded-lg border border-line bg-surface p-pad shadow-sm`
- Badges: `inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3`
- Color tokens: `text-ink`, `text-ink-2`, `text-ink-3`, `text-ink-4`, `text-pos`, `text-breach`, `text-caution`
- Form inputs: same `px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px]` pattern
- Responsive grid: `grid-cols-1 sm:grid-cols-2` for detail panels
- Buttons: consistent sizing, disabled states, loading states
- Status dots: `w-1.5 h-1.5 rounded-full bg-pos/bg-breach` for artifact health

**No design changes needed.** Governance UI uses existing Admin design language.

---

## 4. Backend Registry Implementation

### Registry file
`research/finrlx_cpu/exports/export_registry.json`

### Methods added to `FinRLXResearchService`

| Method | Description |
|--------|-------------|
| `load_dataset_export_registry()` | Load from disk; create empty if missing; safe error if corrupt |
| `save_dataset_export_registry(registry)` | Atomic write via temp file + replace |
| `register_dataset_export(export_response)` | Register export in registry after creation |
| `list_dataset_exports(lifecycle_state, limit)` | List from registry, newest first, optional filters |
| `get_dataset_export(export_id)` | Full schema from registry + metadata file enrichment |
| `mark_dataset_export_stale(export_id, reason)` | Set lifecycle_state to "stale", preserve files |
| `verify_dataset_export_artifact(export_id)` | Check metadata/data file existence on disk |
| `rebuild_dataset_export_registry_from_files()` | Scan exports dir, rebuild registry from .meta.json/.json files |
| `_check_artifact_files(export_id, format)` | Check file existence, return relative paths |
| `_exports_dir()` / `_registry_path()` | Path helpers |

---

## 5. Backend API Changes

### New Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/rl/finrlx/dataset-exports/{id}/mark-stale` | Mark export as stale |
| GET | `/api/v1/rl/finrlx/dataset-exports/{id}/verify` | Verify artifact files exist |
| POST | `/api/v1/rl/finrlx/dataset-exports/rebuild-registry` | Rebuild registry from files |

### Enhanced Endpoints

| Method | Path | Enhancement |
|--------|------|-------------|
| GET | `/api/v1/rl/finrlx/dataset-exports` | Now uses registry; supports `?lifecycle_state=&limit=` |
| GET | `/api/v1/rl/finrlx/dataset-exports/{id}` | Now returns from registry with lifecycle_state, artifact health |

---

## 6. Frontend/Admin UI Changes

### API Client
- `listFinrlxDatasetExports(params?)` — with optional lifecycle_state/limit
- `markFinrlxDatasetExportStale(exportId, payload)`
- `verifyFinrlxDatasetExport(exportId)`
- `rebuildFinrlxDatasetExportRegistry(payload)`
- New types: `DatasetExportRegistryEntry`, `DatasetExportVerifyResult`
- Updated: `DatasetExportResponse` with lifecycle_state, artifact_exists, metadata_path, data_path

### Admin UI
- **Registry list**: clickable entries with lifecycle state badges, artifact health dots
- **Export detail panel**: full schema display with safety flags
- **Verify artifact button**: shows metadata/data existence
- **Mark stale control**: acknowledgement checkbox + optional reason
- **Rebuild registry control**: acknowledgement checkbox + rebuild button
- All mobile/tablet safe (flex-wrap, break-all, stacking on small screens)

---

## 7. Registry Schema

```json
{
  "version": 1,
  "updated_at": "ISO timestamp",
  "exports": [
    {
      "export_id": "uuid",
      "created_at": "...",
      "updated_at": "...",
      "status": "completed",
      "lifecycle_state": "active|stale",
      "name": "...",
      "row_count": 0,
      "date_range": {"start_date": "...", "end_date": "..."},
      "assets": [],
      "export_format": "jsonl|json",
      "export_path": "research/finrlx_cpu/exports/...",
      "metadata_path": "research/finrlx_cpu/exports/...",
      "data_path": "research/finrlx_cpu/exports/...",
      "checksum": "...",
      "fingerprint": "...",
      "research_only": true,
      "offline_only": true,
      "shadow_only": true,
      "no_production_influence": true,
      "not_eligible_for_promotion": true,
      "artifact_exists": true,
      "metadata_exists": true,
      "data_exists": true
    }
  ]
}
```

---

## 8. Path Safety Model

- All paths in registry and API responses are **relative** (e.g. `research/finrlx_cpu/exports/...`)
- No absolute paths (`C:\`, `/home/`, etc.) ever stored or returned
- No secrets, env vars, credentials, or broker config in registry
- Registry reads/writes only within `research/finrlx_cpu/exports/`
- Atomic writes via temp file + `os.replace()`

---

## 9. Artifact Health Model

Each export tracks three booleans:
- `metadata_exists` — metadata file found on disk
- `data_exists` — data file found on disk
- `artifact_exists` — both metadata and data exist

Verify endpoint refreshes these and persists to registry.
Missing files do not crash — they produce warnings.

---

## 10. Operator Controls

| Control | Behavior |
|---------|----------|
| Verify Artifact | Strictly read-only: checks file existence on disk, does not modify registry, does not update timestamps. Returns live filesystem state alongside registry snapshot values. |
| Mark Stale | Sets lifecycle_state="stale", preserves files, requires acknowledgement |
| Rebuild Registry | Scans exports dir, rebuilds from metadata files, requires acknowledgement |

None of these controls can promote, publish, train, benchmark, or influence production.

---

## 11. Safety and Isolation Analysis

- All registry entries forced to: research_only=true, offline_only=true, shadow_only=true, no_production_influence=true, not_eligible_for_promotion=true
- mark-stale does NOT delete files
- verify is read-only
- rebuild only scans `research/finrlx_cpu/exports/`
- No `/rl/execute` endpoint added
- No broker execution
- No production neural inference
- Recommendations, overview, publication unaffected (tested)

---

## 12. Tests Added

**File:** `backend/tests/test_phase8i2_dataset_export_governance.py` — 24 tests

| # | Test |
|---|------|
| 1 | Registry created when missing |
| 2 | Export registers in registry |
| 3 | List uses registry, newest first |
| 4 | Get by ID returns full schema from registry |
| 5 | Registry paths are relative |
| 6 | Registry never stores absolute paths |
| 7 | Registry never stores secrets |
| 8 | Mark stale requires acknowledgement |
| 9 | Mark stale changes lifecycle state |
| 10 | Mark stale invalid ID returns 404 |
| 11 | Verify reports existing files |
| 12 | Verify reports missing files safely |
| 13 | Verify invalid ID returns 404 |
| 14 | Rebuild requires acknowledgement |
| 15 | Rebuild scans exports directory |
| 16 | Corrupt registry returns safe warning |
| 17-21 | Safety regressions (recommendations, overview, publication, promotion, training, benchmark) |
| 22 | /rl/execute remains absent |
| 23 | Phase 8I.1 exports still work |

---

## 13. Test Results

### Phase 8I + 8I.2 targeted
```
46 passed in 25.95s
```

### Phase 8 full regression (8A+8B+8E+8F+8I+8I.2)
```
132 passed in 64.74s
```

---

## 14. Frontend Build/Typecheck/Lint Results

```
build: PASS (compiled successfully, 11/11 pages, /admin 17.9kB)
typecheck: PASS (zero errors)
lint: PASS (zero warnings/errors)
```

---

## 15. Unsafe Language Grep Result

```
Searched: admin/page.tsx, api.ts, rl_finrlx.py, finrlx_research.py
Patterns: buy, sell, trade now, execute trade, live signal, best investment, production alpha, deploy policy
Result: No matches
```

---

## 16. Production/Container Persistence Note

The export registry and artifact files are stored on the local filesystem at
`research/finrlx_cpu/exports/`. In containerized/Railway deployments:
- These files may be **ephemeral** unless a persistent volume is configured
- The rebuild-registry endpoint can reconstruct the registry from surviving files
- Loss of files means loss of export artifacts (not production data)

---

## 17. Known Limitations

1. Registry is file-backed, not database-backed — suitable for single-instance local use
2. No concurrent write locking (atomic replace is sufficient for local use)
3. Export artifacts may not persist in container restarts without volume mounts
4. No automated stale detection or cleanup
5. Registry entries are not deduplicated across rebuild operations (idempotent by export_id)

---

## 18. Stop/Go Recommendation

**GO** — Phase 8I.2 (with corrupt-registry + verify-readonly fixes) is complete:
- 55/55 Phase 8I+8I.2 tests pass
- 141/141 Phase 8 regression tests pass
- Frontend build/typecheck/lint clean
- No unsafe language
- Registry persistence verified
- Corrupt-registry protection verified
- Verify endpoint is strictly read-only (tested)
- All safety invariants preserved

### Corrupt-Registry Fix (8I.2-fix)

1. `load_dataset_export_registry()` now sets `registry_corrupt: true` on corrupt state
2. `register_dataset_export()` skips save when registry is corrupt; export files are still created
3. Export response includes warning about skipped registry
4. `list/get/verify/mark-stale` endpoints return HTTP 409 when registry is corrupt
5. Only `rebuild-registry` with explicit acknowledgement can overwrite a corrupt registry
6. Corrupt error responses contain no secrets or absolute paths
7. 7 new tests verify all corrupt-registry behaviors

### Verify Read-Only Fix (8I.2-fix2)

1. `verify_dataset_export_artifact()` no longer mutates registry entries or calls `save_dataset_export_registry()`
2. Artifact health is computed dynamically from the filesystem at request time
3. Response includes `registry_snapshot_*` fields showing the stored registry state for comparison
4. 2 new tests prove registry file content is unchanged after verify (both existing and missing artifacts)
