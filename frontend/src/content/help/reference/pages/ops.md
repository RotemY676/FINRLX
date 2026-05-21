---
title: Ops command
summary: Publication queue, data feeds, engines, policy breaches, incidents, audit trail.
diataxis: reference
area: reference
updated: 2026-05-22
order: 110
---

The Ops page is the operational command center.

## Sections

### Publication queue

Recommendations waiting to be published, with timestamps and queue-dwell time. Long dwell times indicate publication pipeline congestion.

### Data feeds

Per-feed status with last-reported timestamp, freshness chip, and lag against SLA. UNAVAILABLE means no recent report. Click a feed row for detail and recent error logs. See [Status chips](/help/reference/status-chips).

### Engines

Per-engine status: last training timestamp, last validation Sharpe, currently-deployed version. Stale training is the most consequential warning here — it signals that the engine has not seen recent regime changes.

### Policy breaches

Active breaches across all users / accounts, grouped by constraint. Mirrors the breach list on the [Policies page](/help/reference/pages/policies) at a wider scope.

### Open incidents

Incidents the team is tracking. Each row links to a detail view with timeline, owner, and status.

### Audit trail

The full audit trail in reverse chronology. Filterable by actor (user / system), event type, and date range. The same data backs every [Replay](/help/reference/pages/replay).

## See also

- [Governance and audit](/help/concepts/governance-and-audit) — what the audit trail records.
- [Status chips](/help/reference/status-chips) — the chip catalogue.
