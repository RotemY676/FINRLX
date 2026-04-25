# Phase 8B.2: Audit Persistence Verification Hotfix — Report

**Date:** 2026-04-25
**Status:** Complete

---

## Root Cause

`test_train_creates_audit_events_persisted` did not actually assert audit events existed. It fetched `/api/v1/ops/audit`, filtered for finrlx events, but only asserted `training_status == "completed"` — which proves the API call succeeded, not that audit events were persisted.

## How Audit Persistence Is Now Verified

**Method:** Direct DB query using `test_session_factory` (Option A).

The test queries `AuditEvent` table directly:
```python
events = await db.execute(
    select(AuditEvent)
    .where(AuditEvent.object_type == "finrlx_research")
    .order_by(AuditEvent.occurred_at.desc())
)
```

## Fields Asserted on Requested Event
- `action == "finrlx_train_research_requested"` (exists in DB)
- `details.research_acknowledgement == True`
- `details.safety_flags.research_only == True`
- `details.name` is not None

## Fields Asserted on Completed Event
- `action == "finrlx_train_research_completed"` (exists in DB)
- `details.candidate_id` is not None
- `details.training_run_id` is not None
- `details.safety_flags.research_only == True`
- `details.isolation_checks.promotion_blocked == True`
- `details.production_fingerprints_unchanged` exists
- `details.component_checks.recommendations_current.snapshot_available == True`
- `details.component_checks.publication_status.snapshot_available == True`
- `details.component_checks.overview.snapshot_available == False`
- `details.component_checks.overview.reason` is not None

## Files Changed (2)

```
backend/tests/test_phase8b_finrlx_safety_hardening.py
DOCS/handoff/PHASE_8B2_AUDIT_PERSISTENCE_VERIFICATION_HOTFIX_REPORT.md
```

## Backend Test Results

345 passed, 2 skipped — zero regressions.

## Design Handoff Review

**Files reviewed:** `tokens.css`, `styles.css`, `Design System.html`. No frontend changes. **No new UI style.**

## Safety Confirmations

- No live RL — CONFIRMED
- No broker execution — CONFIRMED
- No recommendation pollution — CONFIRMED
- No overview pollution — CONFIRMED
- No publication influence — CONFIRMED
- All outputs research/offline/shadow only — CONFIRMED
- design/handoff-package reviewed — CONFIRMED
