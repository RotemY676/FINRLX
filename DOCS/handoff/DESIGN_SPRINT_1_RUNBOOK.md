# Design Sprint 1 Runbook

**Updated:** 2026-04-24

## Startup

Same as before — no new infrastructure.

```bash
# Terminal 1: Backend
cd backend
pip install -r requirements.txt
rm -f finrlx_dev.db
alembic upgrade head
python -m seed
uvicorn app.main:app --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

## What Visual Differences Should Now Be Visible

### Shell (all pages)
- **TopBar** at the top: brand mark, "QuantPipeline · decision", breadcrumbs showing current workspace, scope chips (Regime, Horizon, Universe), search placeholder, notification bell with red dot, context pane toggle, avatar
- **Left navigation** upgraded: real SVG icons (not letter badges), "Workspaces" section with 9 items + badge counts, "Operations" section with Ops command, "Saved views" section with color-coded view names
- **Sidebar collapse**: click the panel-left icon in TopBar to toggle sidebar between full and icon-only mode
- **Context pane**: click panel-right icon in TopBar to toggle. Now shows tabbed interface (Risk / Provenance / Compare / Notes) instead of single-content pane

### Overview (/)
- **KPI strip** at top: 6 cards (Positions, Publishable, Warnings, Freshness, Coverage, Recommendations) with accent-colored values using display font (Fraunces)
- **Recommendation card** with confidence rings (circular SVG indicators) instead of horizontal bars
- **Regime & signal posture** section with regime label, signal posture list, sector tilt — marked "Pending backend integration"
- **Activity feed** with typed event icons — marked "Pending backend integration"

### Decision Workspace (/decision)
- **Hero strip** with rec ID, status pill, thesis narrative, stance metrics using display font
- **Action bar**: "Save as current thesis" (primary blue), "Promote to paper", "Defer decision", Compare, Replay links
- **Evidence narrative** section showing top 5 positions with numbered entries — marked "Partial"
- **Risk constraints** section with constraint dots and adjustments
- **Scenario controls** section shell — marked "Pending"
- **Engine disagreement** section shell — marked "Pending"
- Pipeline stage cards with new token styling

### Comparison (/comparison)
- KPI cards with display font for total active weight and concentration
- Confidence rings in the metrics row
- Stance pills on table rows (green/red/gray soft backgrounds)
- **Multi-engine matrix** section shell — marked "Pending"

### Admin / Ops (/admin)
- Now a real Ops Command Center with 6 sections: Publication Queue, Data Feeds, Engine Health, Breach Watch, Incidents, Audit Trail
- Each section has placeholder metrics and "Pending backend integration" notes
- Uses icon system and StatusBadge components

### All pages
- **Typography**: Inter Tight (body), Fraunces (display/hero numbers), JetBrains Mono (data values)
- **Colors**: oklch-based tokens — cool neutral backgrounds, disciplined blue primary, measured green/amber/red status colors
- **Cards**: `rounded-lg border border-line bg-surface shadow-sm`
- **Spacing**: density-aware padding/gaps via CSS variables

## Which Areas Are Real Data vs Pending

| Area | Status |
|---|---|
| KPI strip values (positions, warnings) | **Real** — from API |
| Recommendation card + confidence | **Real** — from API |
| Regime & signal posture | **Pending** — illustrative data, backend not wired |
| Activity feed | **Pending** — structural shell only |
| Decision hero strip | **Real** — from API |
| Evidence narrative | **Partial** — uses weight rationales, full evidence API pending |
| Action bar buttons | **UI only** — no publish/defer state machine |
| Scenario controls | **Pending** — backend engine required |
| Engine disagreement | **Pending** — per-engine signal data required |
| Risk constraints | **Partial** — shows current risk overlay data |
| Pipeline stages | **Real** — from API |
| Weights chart + table | **Real** — from API |
| Comparison weights | **Real** — from API |
| Multi-engine matrix | **Pending** — per-engine data required |
| Ops Command Center sections | **Pending** — all sections structural shells |
| Scope chips in TopBar | **Illustrative** — regime/horizon/universe hardcoded |
| Nav badge counts | **Illustrative** — not from API |

## Troubleshooting

**Fonts don't load:**
- Inter Tight and Fraunces are loaded via Google Fonts import in globals.css
- Requires internet access; will fall back to system fonts offline

**Colors look wrong / no styling:**
- The new token system uses oklch colors via CSS custom properties
- Ensure the browser supports oklch (all modern browsers do)
- If running older browsers, colors may not render correctly

**Dark theme:**
- Not active by default. Can be toggled by adding `data-theme="dark"` to `<html>` element via browser dev tools

**Sidebar badge counts are static:**
- Badge counts (4, 12, 2, 1) are hardcoded in the sidebar component
- They will become dynamic when backend provides workspace counts

**Context pane tabs show "Awaiting backend integration":**
- Risk tab shows illustrative data
- Provenance, Compare, Notes tabs are structural shells
