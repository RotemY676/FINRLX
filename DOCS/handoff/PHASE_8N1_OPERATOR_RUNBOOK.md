# Phase 8N.1A — Operator Runbook: Research Registry Persistence

## Overview

The FINRLX research workflow uses local file-backed JSON registries under
`research/finrlx_cpu/` for tracking dataset exports, experiments, comparisons,
and readiness reviews. This is suitable for local/offline/single-instance research
but has durability implications in container deployments.

**This system is research-only, offline-only, and has no production influence.**

---

## Local Development Behavior

- Registries are stored in `research/finrlx_cpu/{exports,experiments,comparisons,readiness}/`
- Each registry is a JSON file (e.g., `export_registry.json`)
- Data persists across server restarts (files on local disk)
- Write operations use atomic tmp-file + rename pattern
- No database tables involved for registry storage
- **State is durable** on local development machines

## Railway/Container Behavior WITHOUT Persistent Volume

- Container filesystem is ephemeral
- Registry files are created during runtime but **lost on redeploy**
- Each new deployment starts with empty registries
- The Admin persistence panel will show warnings about this
- `is_persistent_volume_configured: false` in the API response
- **State is NOT guaranteed durable**

## Railway/Container Behavior WITH Persistent Volume

- If `RAILWAY_VOLUME_MOUNT_PATH` is set and the research directory
  is configured to use it, registry files persist across redeploys
- The Admin persistence panel will show `is_persistent_volume_configured: true`
- **State durability depends on volume configuration**

## What State Is Durable Today

| State | Storage | Durable? |
|-------|---------|----------|
| Recommendations, queue, audit | Postgres DB | Yes |
| Policy rules, breaches | Postgres DB | Yes |
| Incidents, system health | Postgres DB | Yes |
| ML/RL benchmark reports | Postgres DB | Yes |
| **Dataset export registries** | **Local JSON files** | **Local only** |
| **Experiment registries** | **Local JSON files** | **Local only** |
| **Comparison registries** | **Local JSON files** | **Local only** |
| **Readiness review registries** | **Local JSON files** | **Local only** |
| Export data files (.jsonl/.json) | Local filesystem | Local only |

## What State Is NOT Guaranteed Durable

- All `research/finrlx_cpu/*` registry JSON files
- All exported dataset files
- Experiment metadata and results stored in JSON registries
- Comparison snapshots and rankings
- Readiness review checklists and findings

## How to Interpret the Admin Persistence Panel

The "Research Storage & Deployment" panel in the Safety/Ops tab shows:

1. **Storage mode** — Currently always "local file backed"
2. **Database backed** — Currently "No" (registries are not in Postgres)
3. **Persistent volume** — "Yes" if `RAILWAY_VOLUME_MOUNT_PATH` is detected
4. **Environment** — "local", "railway", "container", or "unknown"
5. **Containerized** — Whether the system appears to run in a container
6. **Registry statuses** — Per-registry health (ok/missing/degraded/unavailable)

### Status meanings:
- **ok** — Directory and registry file exist, readable, writable, not corrupt
- **missing** — Directory or registry file does not exist yet (will be created on first use)
- **degraded** — Registry file exists but is corrupt or unreadable
- **unavailable** — Directory is not accessible

### Warning examples:
- "Container deployment detected without persistent volume" — registry data may be lost
- "Registry file is corrupt" — rebuild-registry may be needed
- "Directory not writable" — exports/experiments cannot be created

## API Endpoint

```
GET /api/v1/rl/finrlx/persistence/status
```

Returns the full persistence status as JSON. Read-only. Does not modify registries.

## Future Recommended Path

**Phase 8N.2 — Postgres Registry Metadata Mirror**

Mirror registry metadata into Postgres tables for durability, while keeping
file-backed JSON as the primary store. This provides a safety net for container
deployments without requiring a full migration.

**This is NOT implemented in Phase 8N.1A.** The current phase only exposes
the truth about persistence to operators and the UI.
