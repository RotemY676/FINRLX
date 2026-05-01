# Phase 8N.2A — Operator Runbook: Postgres Registry Metadata Mirror

## Overview

Phase 8N.2A adds a Postgres-backed metadata mirror for research registry entries.
This mirrors sanitized metadata summaries — not full artifacts or raw payloads.

**This system is research-only, offline-only, and has no production influence.**

---

## What IS Mirrored to Postgres

- Sanitized metadata summaries for each registry item:
  - registry kind (dataset_export, experiment, comparison, readiness_review)
  - record ID, hash/fingerprint, lifecycle state
  - display name (truncated)
  - sanitized paths (no secrets)
  - summary statistics (row counts, metric names, experiment counts)
  - warnings and limitations lists
  - mirror status and timestamps
  - safety flags (always research_only=true, offline_only=true, no_production_influence=true)

## What is NOT Mirrored to Postgres

- Full raw registry JSON payloads
- Exported dataset files (.jsonl, .json)
- Experiment result data files
- Arbitrary nested parameters or configurations
- Secrets, tokens, passwords, API keys, or DATABASE_URL values
- Any data that could influence production recommendations or publication

## Local JSON Registries Remain Operational Source

In this phase, the local file-backed JSON registries under `research/finrlx_cpu/`
remain the operational source for the research workflow. The database mirror is
a durability/visibility layer only.

The research workflow reads from and writes to local JSON files.
The database mirror is populated by explicit operator sync actions.

## How to Run Dry-Run Sync

### From Admin UI
1. Navigate to Safety/Ops → Research Storage & Deployment panel
2. Expand details
3. In "Database Metadata Mirror" section, click "Dry-run sync"
4. Review the result: candidates seen, would-insert, would-update counts

### From API
```
POST /api/v1/rl/finrlx/registry-metadata/sync
Body: {"dry_run": true}
```

## How to Run Metadata Sync

### From Admin UI
1. Same panel as above
2. Click "Sync metadata"
3. Review: inserted count, updated count

### From API
```
POST /api/v1/rl/finrlx/registry-metadata/sync
Body: {"dry_run": false}
```

## How to Check Mirror Status

### From Admin UI
The persistence panel shows:
- Total mirrored records
- Counts by registry kind
- Last sync timestamp
- Artifact DB storage: No
- Local registries operational: Yes

### From API
```
GET /api/v1/rl/finrlx/registry-metadata/status
```

## How to Interpret Counts/Statuses

| Mirror Status | Meaning |
|---------------|---------|
| active | Registry item exists and was synced successfully |
| stale | Registry item was previously synced but source is now marked stale |
| missing_source | Mirror row exists but source registry item was not found in last sync |
| error | Source registry was corrupt or unreadable |
| skipped | Item was intentionally skipped during sync |

## This Phase Does NOT Make Research Workflow Production-Influencing

- No production recommendation, publication, or overview flow uses this metadata
- The model has `no_production_influence=True` as a non-nullable column default
- Production API files (overview.py, recommendations.py, publication.py) do not
  import the mirror model or service — this is tested in the isolation test

## Future Recommended Path

Phase 8N.2B — Automatic sync hooks or scheduled background sync.
Phase 8N.3 — Optionally, migrate operational registry source to Postgres
(not planned for this phase).
