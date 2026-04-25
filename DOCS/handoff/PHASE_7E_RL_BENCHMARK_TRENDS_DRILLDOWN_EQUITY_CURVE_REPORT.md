# Phase 7E: RL Benchmark Trends, Drill-down & Equity Curve — Report

**Date:** 2026-04-25
**Phase:** 7E — Benchmark history, drilldown, equity curve, trends
**Status:** Complete

---

## 1. Executive Summary

Phase 7E extends the single-benchmark view from Phase 7D into a full forensic analysis surface with benchmark history (selectable reports), report drill-down, per-agent portfolio value curves (SVG sparklines), per-agent forensic summaries via `forensic_summary_by_agent`, and a cross-benchmark trend table. All outputs remain offline/shadow only.

---

## 2. Files Changed

### Backend (2 modified)
```
backend/app/services/rl_benchmark.py   — collect per-agent forensic rows into forensic_summary_by_agent (cap 50/agent)
backend/app/api/v1/rl_benchmark.py     — expose forensic_summary_by_agent in API response
```

### Frontend (2 modified)
```
frontend/src/services/api.ts           — added forensic_summary_by_agent field to RLBenchmarkReport type
frontend/src/app/admin/page.tsx        — benchmark history panel, selectable drilldown, equity curve, trend table
```

### Documentation (1 created)
```
DOCS/handoff/PHASE_7E_RL_BENCHMARK_TRENDS_DRILLDOWN_EQUITY_CURVE_REPORT.md
```

---

## 3. Backend Changes

- `rl_benchmark.py` service: collects forensic rows for ALL agents (not just first), stored as `forensic_summary_by_agent` in `dataset_lineage` JSON, capped at 50 rows per agent. Existing `forensic_summary` (first-agent-only, capped at 100) preserved for backward compatibility.
- `rl_benchmark.py` API: added `forensic_summary_by_agent` field to `_report_dict` response.

---

## 4. Frontend/UI Surfaces Changed

### Benchmark History Panel (NEW)
- Lists up to 8 recent benchmark reports
- Shows: status badge, name, date window, agent count, complete/partial badge
- Click to select — selected report highlighted with primary border
- Replaces the old single-benchmark view with a selectable pattern

### Selected Benchmark Drill-down (ENHANCED)
- Shows all metadata: ID, name, status, complete/partial, environment_key, created_at
- Full 6-safety-badge row
- Metadata row: window, agents executed, skipped count, environment, created timestamp
- Skipped agents warning panel
- Agent comparison table (unchanged from 7D.1: 4-metric highlights)
- Reward breakdown table
- Equity curve (NEW)
- Forensic step summary
- Warnings panel

### Equity / Portfolio Value Curve (NEW)
- SVG polyline sparklines per agent (from `forensic_summary_by_agent` or `forensic_summary`)
- Shows agent name, sparkline, final portfolio value
- Dashed reference line at 100 (starting value)
- Final value colored green (>=100) or red (<100)
- Honestly labels data source: per-agent when available, first-agent-only when not
- Labeled "Offline Forensic Portfolio Value Curve" — "Not a live signal"

### Benchmark Trend Table (NEW)
- Cross-benchmark comparison across recent reports
- Columns: benchmark ID, window, agent, return, reward, drawdown, turnover
- Flat-mapped: each benchmark × each agent = one row
- Up to 5 benchmarks shown
- Labeled "Offline Benchmark Trend" — "not live performance"

### Empty State (PRESERVED)
- "No offline benchmarks have been run yet" with explanation text

---

## 5. API/Type Changes

Added to `RLBenchmarkReport`:
```typescript
forensic_summary_by_agent?: Record<string, RLForensicStep[]> | null;
```

---

## 6. Design Handoff Review

**Design files reviewed:** `HANDOFF.md`, `INDEX.md`, `tokens.css`, `styles.css`, `Ops.html`, `Engine Comparison.html`, `Backtests.html`, `Design System.html`

**Patterns reused:**
- Card: `rounded-lg border border-line bg-surface p-pad shadow-sm`
- Selectable list: `bg-primary-soft border border-primary` for selected, `hover:bg-surface-3` for others (same as backtests/replay selector)
- Table: `text-[11px]`, sticky thead, `border-b border-line/30` rows
- Badge: `inline-flex px-2 py-0.5 rounded-md text-[10px] font-medium`
- Status: StatusBadge component
- Icon: Icon component with `text-accent`, `text-ink-3`
- Sparkline: SVG polyline with oklch token colors (`0.52 0.17 255` for primary line, `0.92 0.008 240` for reference)
- History icon: reused `history` icon, trend icon: reused `trend-up` icon

**No unrelated UI style was introduced.** All new sections follow existing Admin/Ops card/table/badge conventions.

---

## 7. Tests Run

**Backend:** 306 passed, 2 skipped — zero regressions
**Frontend:** Compiled successfully, types checked, 11/11 pages generated. `/admin` = 9.49 kB.

---

## 8. Production Smoke Commands

```powershell
$base = "https://backend-production-aab8.up.railway.app/api/v1"
$frontend = "https://frontend-production-7e8b1.up.railway.app"

Invoke-RestMethod "$base/health"
Invoke-RestMethod "$base/rl/adapter/status"

$reports = Invoke-RestMethod "$base/rl/benchmarks"
$reports.data.Count
$latestId = $reports.data[0].id
$latest = Invoke-RestMethod "$base/rl/benchmarks/$latestId"

$latest.data.status
$latest.data.is_complete_comparison
$latest.data.metrics_by_agent.PSObject.Properties.Name
$latest.data.safety_flags | ConvertTo-Json -Depth 5
$latest.data.forensic_summary | Select-Object -First 3
if ($latest.data.forensic_summary_by_agent) {
  $latest.data.forensic_summary_by_agent.PSObject.Properties.Name
}

try { Invoke-RestMethod "$base/rl/execute" -Method POST -ContentType "application/json" -Body "{}" } catch { $_.Exception.Response.StatusCode.value__ }

Invoke-RestMethod "$base/overview"
Invoke-RestMethod "$base/recommendations/current"
Invoke-RestMethod "$base/publication/status"
Invoke-WebRequest "$frontend/admin" -UseBasicParsing
```

---

## 9. Manual UI Inspection

Navigate to `/admin` → scroll to RL sections:
1. **Benchmark History** — list of selectable reports with status/date/agents
2. Click a report → **Drill-down** shows all metadata, safety badges, tables
3. **Equity curve** — SVG sparklines per agent with reference line at 100
4. **Trend table** — cross-benchmark comparison below the drilldown
5. Verify all 6 safety badges visible
6. Verify no buy/sell/trade/execute language

---

## 10. Known Limitations

1. No Recharts-based chart — uses lightweight SVG sparklines (no dependency added)
2. Equity curve is per-agent sparkline, not overlaid multi-line chart
3. Trend table limited to 5 most recent benchmarks
4. History panel limited to 8 most recent reports
5. forensic_summary_by_agent capped at 50 rows per agent
6. No "Run benchmark" trigger button in UI (API only)
7. No cross-benchmark date-range filtering in UI

---

## 11. Safety Confirmations

- **No live RL added** — CONFIRMED
- **No broker execution added** — CONFIRMED
- **No auto-trading added** — CONFIRMED
- **No recommendation pollution** — CONFIRMED
- **No overview pollution** — CONFIRMED
- **No publication influence** — CONFIRMED
- **RL remains offline/shadow only** — CONFIRMED
- **design/handoff-package reviewed** — CONFIRMED

---

## 12. Recommended Next Phase

```
Phase 7F: [Future — FINRL-X Neural Training & Advanced Agents]
Do not start without explicit instruction.
```
