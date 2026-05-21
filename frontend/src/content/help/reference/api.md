---
title: REST API
summary: The /api/v1/* endpoints used by the workspace — methods, payloads, auth.
diataxis: reference
area: reference
updated: 2026-05-22
order: 4
---

The FINRLX backend exposes a REST surface under `/api/v1/`. The workspace is itself a consumer of this API; everything you can do in the UI is reachable from a script with the right credentials.

This reference is the catalog of endpoints, grouped by area (Profile, Recommendations, Backtests, Policies, Universe, Workspace), with request and response shapes for each.
