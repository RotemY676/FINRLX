# Phase 8N.1A — Persistence Status, Deployment Warnings & Operator Runbook

## Scope

Deployment-reality and truthfulness gate for FINRLX research workflow registries.
Exposes the truth about local file-backed JSON registries to the backend API,
Admin UI, tests, and operator documentation.

**Not in scope:** Postgres migration, registry rewrite, production RL, live trading,
broker execution, production signal influence, or recommendation influence.

## Files Changed

### Backend
- `backend/app/services/finrlx_research.py` — Added `get_persistence_status()` static method
- `backend/app/api/v1/rl_finrlx.py` — Added `GET /api/v1/rl/finrlx/persistence/status` endpoint
- `backend/tests/test_phase8n1_persistence_deployment.py` — 20 tests covering schema, safety, environment detection, corruption handling, volume containment, secret safety

### Frontend
- `frontend/src/services/api.ts` — Added `FinrlxPersistenceStatus`, `FinrlxRegistryPersistenceStatus` types and `getFinrlxPersistenceStatus()` client method
- `frontend/src/app/admin/_components/ResearchPersistencePanel.tsx` — New panel component
- `frontend/src/app/admin/_components/steps/PublicationQueuePanel.tsx` — Integrated persistence panel

## Backend Endpoint Summary

**Endpoint:** `GET /api/v1/rl/finrlx/persistence/status`

**Behavior:**
- Read-only inspection of all 4 research registry directories and files
- Safe write probe (creates + immediately deletes temp file) for writability check
- Environment detection via Railway/container env vars
- Path sanitization (project-relative only, no secrets)
- Does not modify registry files
- Does not rebuild registries
- Reports corrupt registries as degraded without modifying them

**Response fields:**
- `storage_mode`, `storage_root`, `is_local_file_backed`, `is_database_backed`
- `is_persistent_volume_configured` — env var exists
- `storage_root_uses_persistent_volume` — actual storage is inside volume
- `persistent_volume_mount_path` — sanitized mount path or null
- `deployment_environment`, `appears_containerized`
- `registry_statuses[]` (per-registry directory/file health, item counts, warnings)
- `warnings[]`, `limitations[]`, `recommended_next_action` (string | null)
- `research_only: true`, `offline_only: true`, `no_production_influence: true`

**Truthful volume detection:**
- `is_persistent_volume_configured` only means the env var exists
- `storage_root_uses_persistent_volume` verifies the storage root is under the volume
- If volume exists but storage is not inside it, a specific warning is returned

## Frontend UI Summary

**Component:** `ResearchPersistencePanel`
**Location:** Rendered inside Safety/Ops tab (PublicationQueuePanel)

**Displays:**
- Storage mode, database backed, persistent volume, environment, containerized, storage root
- Per-registry status rows with health indicators and item counts
- Warnings with caution styling
- Recommended next action
- Limitations list
- Safety invariant badges (research only, offline only, no production influence)
- Expand/collapse for detailed registry status
- Refresh button for live status check

## Tests Run

### Phase 8N.1 targeted (20 tests)
```
20 passed in 2.18s
```

### Full Phase 8 regression (286 tests)
```
286 passed
```

### Frontend
```
Build: PASS
TypeCheck: PASS
Lint: No ESLint warnings or errors
```

### Unsafe wording grep
```
No matches found.
```

## Safety Invariant Confirmation

- [x] research_only: true — enforced in endpoint response and UI badges
- [x] offline_only: true — enforced in endpoint response and UI badges
- [x] no_production_influence: true — enforced in endpoint response and UI badges
- [x] No connection to /overview, /recommendations, or /publication
- [x] No broker execution
- [x] No live RL execution
- [x] No production neural inference
- [x] No unsafe wording (buy, sell, trade now, etc.)

## Known Limitations

1. Registries remain local file-backed JSON — not Postgres-backed
2. Container/Railway deployments may lose registry state on redeploy without persistent volume
3. No automatic backup mechanism for registry files
4. State is not replicated across instances
5. Write probe creates and deletes a temp file — may fail on read-only filesystems

## Recommended Next Phase

Phase 8N.2 — Postgres Registry Metadata Mirror (shadow copy of registry metadata into
database tables for durability, without changing the file-backed primary store).
