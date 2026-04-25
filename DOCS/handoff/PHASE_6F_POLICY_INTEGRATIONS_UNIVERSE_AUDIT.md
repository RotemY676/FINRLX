# Phase 6F: Policy, Integrations & Universe — Implementation Audit

**Date:** 2026-04-25

---

## 1. Current Policy/Breach Model — PARTIAL

**What exists:**
- `PolicyBreach` table (ops.py): kind, label, utilization, trend, severity, related, is_active
- Seeded breaches: 3 illustrative entries (sector cap, single-name, energy exposure)
- Publication gates reference `PolicyBreach` for blocking (severity=="breach", is_active==True)
- Pipeline risk overlay uses hardcoded constants (MAX_POSITION_WEIGHT=0.15, CASH_RESERVE=0.05, etc.)
- Publication gates use hardcoded thresholds (MIN_MODEL_CONFIDENCE=0.25, MIN_DATA_CONFIDENCE=0.50, etc.)

**What is missing:**
- No editable policy rules table — all thresholds are hardcoded in Python constants
- No policy rule history (audit trail for threshold changes)
- No structured policy categories
- No way for an operator to change a threshold without code deployment

**Assessment:** FAIL — needs policy_rules + policy_rule_history tables

---

## 2. Current Incidents/Breaches Endpoints — PASS

- GET /ops/breaches returns active policy breaches
- GET /ops/incidents returns open incidents
- POST /ops/incidents/{id}/resolve resolves incidents
- Publication gates check critical incidents (severity<=2) and active breaches
- Breach Watch section in Admin UI shows utilization gauges

**Assessment:** Working as designed. Breaches are seeded/demo.

---

## 3. Current Publication Gates — PARTIAL

10 gates exist in PublicationService.evaluate_gates():
1. lineage, 2. signals, 3. weights, 4. position_cap (hardcoded 0.15), 5. model_confidence (0.25), 6. data_confidence (0.50), 7. operational_confidence (0.50), 8. feature_freshness, 9. critical_incidents, 10. policy_breaches

**What is missing:** Gates don't reference configurable policy rules. All thresholds are Python constants.

**Safe approach:** Policy rules can be created and queried. Gates can expose which policy rule keys they reference. Full integration into gate evaluation is optional for 6F (too risky to change working publication flow).

---

## 4. Current Source/Ingestion/Manifest Tables — PASS

- `IngestionManifest`: source, kind (bars/news), status, asset_count, row_count, date range
- `DataFeed`: name, status, lag, coverage, slo (seeded illustrative data)
- `MarketBar`, `NewsEvent`: real ingested data from local adapter
- IngestService generates bars/news from deterministic local adapter

**What is missing:** No structured integration/provider registry. DataFeed entries are seeded demo labels (Reuters, Bloomberg, CBOE, etc.) — NOT real integrations.

**Assessment:** Need an integration registry that truthfully distinguishes real local adapters from illustrative/placeholder entries.

---

## 5. Current Universe/Assets — PARTIAL

- `Asset`: 10 seeded large-cap equities with ticker, name, sector
- `Universe`: 1 "US Large Cap Core" universe
- `UniverseMembership`: all 10 assets in one universe
- Pipeline, backtesting, paper all use universe

**What is missing:** No universe coverage/readiness summary. No multi-universe management. No asset coverage breakdown by data domain.

**Assessment:** Need read-only universe endpoints with coverage/readiness data.

---

## 6. Current Admin/Ops Frontend — PASS

Admin page shows: KPI strip, ML Observability card, publication queue, feeds, engines, breaches, incidents, audit trail.

**What is missing:** Policy rules section, integrations readiness, universe readiness.

---

## 7. Design Package Surfaces

**Policy Editor (design/handoff-package/Policy Editor.html):**
- Categories: position, exposure, sector, approval, stoploss, regime
- Rules with field/op/val conditions, action (block/warn/allow), impact analysis
- Author, version, draft mode
- Full editor with toggle, impact preview

**Integrations (design/handoff-package/Integrations.html):**
- Categories: market, alt, fund, news, oms, ware, comms, sso
- Active integrations with status (ok/degraded/paused), lag, coverage, SLO
- Catalog of available integrations
- Schema inspection, credentials, spark chart

**Universe (design/handoff-package/Universe.html):**
- Multiple universes with constituent counts
- Filter by mcap, ADV, liquidity, sector
- Factor z-scores per constituent
- Basket management

---

## Summary

| Area | Status | Safe to Implement | Notes |
|---|---|---|---|
| Policy rules table | FAIL | Yes | New table + service + API |
| Policy rule history | FAIL | Yes | Audit trail for changes |
| Publication gate integration | PARTIAL | Minimal | Expose rule keys, don't change gate logic |
| Integration registry | FAIL | Yes | Truthful provider listing |
| Integration health | PARTIAL | Yes | Extend existing feed data |
| Universe endpoints | PARTIAL | Yes | Read-only coverage/readiness |
| Universe write ops | N/A | Skip | Too risky for 6F |
| Admin UI updates | PARTIAL | Yes | Compact sections |
| Seed updates | Needed | Yes | Default policy rules + integration labels |

**Out of scope for 6F:**
- Full policy editor UI with live impact preview
- Real external provider connections
- Universe write operations (add/remove assets)
- RL integration
- Broker/execution
