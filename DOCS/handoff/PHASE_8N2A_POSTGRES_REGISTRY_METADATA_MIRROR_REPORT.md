# Phase 8N.2A — Postgres Research Registry Metadata Mirror

## Scope

Add a Postgres-backed metadata mirror for the four research registry categories.
The local file-backed JSON registries remain the operational source.
This is a durability/readiness foundation, not a full persistence migration.

**Not in scope:** Full registry migration, artifact storage in DB, production RL,
live trading, broker execution, production signal influence, or promotion workflows.

## Files Changed

### Backend — New
- `backend/app/models/research_registry_metadata.py` — SQLAlchemy model
- `backend/migrations/versions/017_research_registry_metadata.py` — Alembic migration
- `backend/tests/test_phase8n2a_registry_metadata_mirror.py` — 12 tests

### Backend — Modified
- `backend/app/models/__init__.py` — Register new model
- `backend/app/services/finrlx_research.py` — 3 new methods + persistence status update
- `backend/app/api/v1/rl_finrlx.py` — 2 new endpoints

### Frontend — Modified
- `frontend/src/services/api.ts` — Types + API methods for mirror status/sync
- `frontend/src/app/admin/_components/ResearchPersistencePanel.tsx` — Mirror section in UI

## Database Migration Summary

**Table:** `research_registry_metadata`
**Revision:** `017_reg_meta` (down from `016_rl_bench`)

**Columns:** id, registry_kind, record_id, record_hash, record_state, display_name,
source_registry_path, artifact_path, metadata_summary_json, warnings_json,
limitations_json, mirror_status, first_seen_at, last_seen_at, created_at, updated_at,
research_only, offline_only, no_production_influence

**Constraint:** unique(registry_kind, record_id)
**Indexes:** registry_kind, record_id, mirror_status, last_seen_at

## Model Summary

`ResearchRegistryMetadata` — mirrors sanitized metadata summaries from local
JSON registries. Always sets research_only=True, offline_only=True,
no_production_influence=True. Does not store full raw payloads or secrets.

## Endpoint Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/rl/finrlx/registry-metadata/status` | GET | Mirror status with counts, safety flags |
| `/api/v1/rl/finrlx/registry-metadata/sync` | POST | Sync metadata (dry_run default=true) |

## Frontend Summary

- ResearchPersistencePanel expanded with "Database Metadata Mirror" section
- Shows: mirrored records, artifact DB storage (No), local registries operational (Yes)
- Operator actions: Dry-run sync, Sync metadata
- Registry kind breakdown badges
- Explicit wording: metadata only, local registries remain operational source

## Tests Run

### Phase 8N.2A targeted (12 tests)
```
12 passed in 1.35s
```

### Full Phase 8 regression (298 tests)
```
298 passed
```

### Frontend
```
Build: PASS
TypeCheck: PASS
Lint: No ESLint warnings or errors
```

### Unsafe wording grep
```
No matches in edited files.
Pre-existing "buy, sell" comment in unmodified validation.py (Phase 5D).
```

## Safety Invariant Confirmation

- [x] research_only: true — enforced in model defaults, service methods, API responses, UI badges
- [x] offline_only: true — enforced in model defaults, service methods, API responses, UI badges
- [x] no_production_influence: true — enforced in model defaults, service methods, API responses
- [x] is_database_backed_artifact_storage: false — explicitly false in all responses
- [x] local_registries_still_operational_source: true — explicitly true in all responses
- [x] No connection to /overview, /recommendations, or /publication (tested by isolation test)
- [x] No unsafe wording in edited files

## Known Limitations

1. This is a metadata mirror only — artifacts remain local/file-backed
2. Local JSON registries remain the operational source
3. Sync is manual (operator-triggered), not automatic
4. Secret sanitization uses regex patterns — novel secret formats may not be caught
5. Corrupt local registries produce error-status mirror candidates, not reconstructed data

## Recommended Next Phase

Phase 8N.2B — Automatic sync on registry write operations (hook into create/update
flows to mirror metadata immediately) or scheduled background sync.
