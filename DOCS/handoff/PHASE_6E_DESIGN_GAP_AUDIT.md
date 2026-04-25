# Phase 6E: Design Gap Audit

**Date:** 2026-04-25
**Purpose:** Compare current frontend against design/handoff-package and identify gaps.

---

## Overview Page — PARTIAL

**Implemented:** KPI strip, recommendation card, health panel, regime/signal, activity feed, pipeline warnings banner.
**Missing from design:**
- No distinction between published vs pipeline-draft recommendation. Shows "No Recommendation Available" when only draft exists (misleading).
- Freshness/Coverage KPIs are hardcoded (94%, 96%) — not from real data.
- No ML shadow compact summary on overview.
- No source/provenance badge on recommendation card.
**Proposed changes:**
- Show draft recommendation with draft badge + "pending publication" hint instead of empty state.
- Files: `frontend/src/app/page.tsx`

## Decision Workspace — PARTIAL

**Implemented:** Hero strip, confidence trio, evidence, disagreement, warnings, scenario, pipeline stages, metadata, action bar.
**Missing from design:**
- Risk constraints section has hardcoded gauge values (42%, 81%, etc.) not from backend.
- No publication status distinction (draft vs staged vs approved vs published).
- No gate status indicator from publication workflow.
**Proposed changes:**
- Add "approved" and "deferred" to StatusBadge. Already exists — PASS.
- No backend changes needed for risk gauges (known limitation).
- Files: none needed for minimal alignment.

## Engine Comparison — PARTIAL

**Implemented:** Engine matrix, alignment chart, weight comparison, position detail.
**Missing from design:**
- ML shadow engine not labeled as shadow/experimental in the matrix.
- No "live influence: off" indicator when ML engine appears.
- Empty state shows "No Recommendation to Compare" but engine data may exist independently.
**Proposed changes:**
- Add shadow/experimental badge to ML engine rows in the matrix.
- Files: `frontend/src/app/comparison/page.tsx`

## Admin/Ops — PASS

**Implemented:** KPI strip, publication queue, feeds, engines, breaches, incidents, audit, ML observability card.
**Gap:** Seeded ops data (queue items, feeds, breaches) is from fixtures but displayed without "demo/seeded" label. Minor.
**Proposed changes:** None required for minimal alignment.

## Backtests — PARTIAL

**Implemented:** Experiment list, source_type badges (Pipeline/Seed/Demo), metrics, equity curve, config, warnings, demo banner.
**Missing from design:**
- No lineage_available indicator.
- No decision_count or market_bar_window display.
- No provenance detail (recommendation_ids, feature_set_ids, signal_run_ids).
- source_type badge uses `(item as any)` cast — not typed.
**Proposed changes:**
- Add provenance fields to BacktestDetail type and display in config section.
- Type source_type properly in api.ts.
- Files: `frontend/src/services/api.ts`, `frontend/src/app/backtests/page.tsx`

## Replay — PARTIAL

**Implemented:** Replay list, detail, confidence, warnings, positions, stage snapshots.
**Missing from design:**
- No seeded/demo warning for non-pipeline replays.
- No feature_set / signal_run lineage display.
- No source provenance badge.
**Proposed changes:**
- Show seeded data warning when replay has no lineage.
- Files: `frontend/src/app/replay/page.tsx`

## Paper Portfolio — PARTIAL

**Implemented:** Holdings, drift, events, invested/cash summary.
**Missing from design:**
- No source_type badge (recommendation_paper / test_paper / seed_demo).
- No source_recommendation_id display.
- No portfolio_value display.
- No performance summary (total return, Sharpe, etc.).
- No trade count or attribution summary.
- No warning for test_paper (created with allow_unpublished).
**Proposed changes:**
- Add source badge and portfolio value.
- Add performance summary section if data available.
- Type source fields in api.ts.
- Files: `frontend/src/services/api.ts`, `frontend/src/app/paper/page.tsx`

## Policy/Governance — N/A

Not implemented as a standalone page. Publication governance is embedded in Decision workspace metadata block and Admin/Ops queue.

## Integrations — N/A

Not implemented. Design exists but no backend support. Out of scope.

---

## Global Token Alignment — PASS

Current tokens.css and tailwind.config.ts already map design/handoff-package/tokens.css accurately:
- oklch color system matches
- Font families match (Inter Tight, Fraunces, JetBrains Mono)
- Border radius tokens match
- Shadow tokens match
- Density spacing tokens match
- Dark theme supported
- No changes needed.

## Badge/Status Standardization — PARTIAL

StatusBadge supports: fresh, published, provisional, published_with_warning, pending, staged, suppressed, stale, draft, completed, failed, running.
**Missing:** approved, deferred, superseded.
**Missing component:** SourceBadge for data provenance (pipeline_backtest, seed_demo, recommendation_paper, test_paper, shadow, experimental).
**Proposed:** Add missing statuses and create a SourceBadge utility.

---

## Summary

| Page | Grade | Action Required |
|---|---|---|
| Overview | PARTIAL | Show draft rec, fix hardcoded KPIs label |
| Decision | PARTIAL | Risk gauges hardcoded (known limitation, skip) |
| Engine Comparison | PARTIAL | Label ML engine as shadow |
| Admin/Ops | PASS | — |
| Backtests | PARTIAL | Type provenance, show lineage fields |
| Replay | PARTIAL | Add seeded data warning |
| Paper Portfolio | PARTIAL | Add source badge, performance, portfolio value |
| Global Tokens | PASS | — |
| Badges | PARTIAL | Add missing statuses + SourceBadge |
