# Design-to-Implementation Bridge

**Date:** 2026-04-24
**Source:** `design/handoff-package/`
**Target:** `frontend/src/` (Next.js 14 + Tailwind + Recharts)

---

## 1. Design Package Inventory

### Files Verified Present

| File | Kind | Purpose |
|---|---|---|
| `HANDOFF.md` | Doc | Full handoff: UX principles, IA, tokens, component inventory, data contracts, stack guidance |
| `INDEX.md` | Doc | Package map in Hebrew+English |
| `styles.css` | Tokens+CSS | Complete design token layer (light+dark), component classes, layout primitives |
| `overview.css` | CSS | Overview-specific styles |
| `ops.css` | CSS | Ops command center styles |
| `shell.jsx` | Component | TopBar, LeftNav (with breadcrumbs, scope chips, search, avatar) |
| `hero.jsx` | Component | HeroStrip (recommendation hero), ConfRing (confidence rings), ActionBar |
| `modules.jsx` | Component | EvidenceCard, RiskCard, DisagreementCard |
| `chart.jsx` | Component | ChartCard (price+band chart with event markers) |
| `scenario.jsx` | Component | ScenarioCard (regime/horizon/stress controls with delta preview) |
| `context.jsx` | Component | ContextPane (tabbed: Risk/Provenance/Compare/Notes) |
| `icons.jsx` | Component | ~40 inline SVG icons (Lucide-style stroke icons) |
| `overview.jsx` | Component | TriageTable, HealthStrip, RegimeStrip, ActivityFeed |
| `overview-app.jsx` | Page | Overview page compositor |
| `app.jsx` | Page | Decision Workspace page compositor |
| `compare-app.jsx` | Page | Engine Comparison page compositor |
| `comparison.jsx` | Component | ComparisonMatrix, AlignmentChart, MethodologyCard, SynthesisCard |
| `ops.jsx` | Component | Ops modules: queue, feeds, engines, breaches, incidents, audit |
| `ops-app.jsx` | Page | Ops Command Center page compositor |
| `tweaks-panel.jsx` | Prototype-only | Runtime design tweaking panel — DO NOT PORT |
| `Overview.html` | Preview | Self-contained HTML preview |
| `Decision Workspace.html` | Preview | Self-contained HTML preview |
| `Engine Comparison.html` | Preview | Self-contained HTML preview |
| `Ops.html` | Preview | Self-contained HTML preview |
| `iOS App.html` | Preview | iOS design canvas preview |
| `ios/ios-shared.jsx` | iOS | Shared iOS tokens, IOSPhone, IOSNav, IOSTabBar |
| `ios/ios-app.jsx` | iOS | iOS canvas compositor |
| `ios/ios-frame.jsx` | iOS | Phone frame renderer |
| `ios/screens-today.jsx` | iOS | Today A + Today B screens |
| `ios/screens-decision.jsx` | iOS | Decision A + B + Scenario + Publish screens |
| `ios/screens-rest.jsx` | iOS | Alerts, Compare, Replay, Watchlist, Notes, Settings |
| `ios/screen-ipad.jsx` | iOS | iPad split view |
| `ios/design-canvas.jsx` | iOS | Canvas layout helper |

### Deliverables Summary
- **4 complete web workspace designs** (Overview, Decision, Comparison, Ops)
- **12 iOS screens** (not in scope for current web implementation)
- **Full design token system** with light+dark themes and 3 density levels
- **~40 icon definitions**
- **Component-level CSS classes** for cards, buttons, pills, badges, tabs, key-value grids
- **Data contracts** (TypeScript interfaces for Recommendation, Evidence, Engine, Risk, Scenario)

### What Is Missing from the Package
- Replay (web) — exists only in iOS, not as a web prototype
- Backtests detail — mentioned as "still to design"
- Paper Portfolio dashboard — mentioned as "still to design"
- Universe browser, Policy editor — mentioned as "still to design"
- Empty/loading/degraded state comprehensive pass — acknowledged as incomplete
- Formal design system project (standalone tokens, motion demos, full state gallery)

---

## 2. Mapping Table

| Design Item | Source File | Target in Codebase | Status | Priority |
|---|---|---|---|---|
| **Design tokens (light)** | `styles.css` `:root` | `tailwind.config.ts` / `globals.css` | Replace existing | **High** |
| **Design tokens (dark)** | `styles.css` `[data-theme="dark"]` | `globals.css` + theme toggle | New — not yet implemented | Medium |
| **Density system** | `styles.css` `[data-density]` | CSS variables + Tailwind | New | Low |
| **Typography (Fraunces display)** | `styles.css` `--font-display` | `tailwind.config.ts` fontFamily | New — current uses Inter only | **High** |
| **Typography (Inter Tight)** | `styles.css` `--font-sans` | `tailwind.config.ts` fontFamily | Enhance existing (Inter → Inter Tight) | **High** |
| **Icon set** | `icons.jsx` | New `components/icons/` | New — current has no icon system | **High** |
| **TopBar** | `shell.jsx` | No equivalent — current has no top bar | New component needed | **High** |
| **LeftNav (enhanced)** | `shell.jsx` | `components/shell/Sidebar.tsx` | Replace existing | **High** |
| **ContextPane (tabbed)** | `context.jsx` | `components/shell/ContextPane.tsx` | Replace existing | **High** |
| **HeroStrip** | `hero.jsx` | `components/recommendation/RecommendationCard.tsx` | Replace existing | **High** |
| **ConfRing** | `hero.jsx` | `components/recommendation/ConfidenceBlock.tsx` | Replace existing | **High** |
| **ActionBar** | `hero.jsx` | No equivalent | New component needed | **High** |
| **StatusPill** | `styles.css` `.status-pill` | `components/recommendation/StatusBadge.tsx` | Replace existing | **High** |
| **EvidenceCard** | `modules.jsx` | No equivalent | New component needed | **High** |
| **RiskCard** | `modules.jsx` | No equivalent — current shows risk as simple text | New component needed | **High** |
| **DisagreementCard** | `modules.jsx` | No equivalent | New component needed | Medium |
| **ChartCard** | `chart.jsx` | `components/charts/WeightsBarChart.tsx` | Replace existing | Medium |
| **ScenarioCard** | `scenario.jsx` | No equivalent | New component needed | Medium |
| **CaveatRow** | `styles.css` `.caveat-row` | `components/recommendation/WarningsBlock.tsx` | Enhance existing | Medium |
| **Card system** | `styles.css` `.card` | Inline Tailwind classes | Enhance — adopt consistent card primitives | **High** |
| **Button system** | `styles.css` `.btn` | No formal button system | New primitive needed | **High** |
| **TriageTable** | `overview.jsx` | `app/page.tsx` (Overview) | Replace existing | **High** |
| **HealthStrip (KPIs)** | `overview.jsx` | `components/overview/HealthPanel.tsx` | Replace existing | **High** |
| **RegimeStrip** | `overview.jsx` | No equivalent | New component needed | Medium |
| **ActivityFeed** | `overview.jsx` | No equivalent | New component needed | Medium |
| **ComparisonMatrix** | `comparison.jsx` | `app/comparison/page.tsx` | Replace existing | **High** |
| **AlignmentChart** | `comparison.jsx` | No equivalent | New component needed | Medium |
| **MethodologyCard** | `comparison.jsx` | No equivalent | New component needed | Medium |
| **SynthesisCard** | `comparison.jsx` | No equivalent | New component needed | Medium |
| **Ops Queue** | `ops.jsx` | `app/admin/page.tsx` (placeholder) | New — replaces placeholder | **High** |
| **Ops Feeds** | `ops.jsx` | No equivalent | New component needed | Medium |
| **Ops Engines** | `ops.jsx` | No equivalent | New component needed | Medium |
| **Ops Breaches** | `ops.jsx` | No equivalent | New component needed | Medium |
| **Ops Incidents** | `ops.jsx` | No equivalent | New component needed | Medium |
| **Ops Audit** | `ops.jsx` | No equivalent | New component needed | Low |
| **ScopeChip** | `styles.css` `.scope-chip` | No equivalent | New primitive needed | Medium |
| **Sparkline** | `overview.jsx` | No equivalent | New chart component | Medium |
| **iOS screens** | `ios/*.jsx` | Not applicable (web only for now) | Deferred | Low |

---

## 3. Screen-by-Screen Mapping

### Overview (`/`)

| Design Element | Design Source | Current Code | Gap |
|---|---|---|---|
| HealthStrip (6 KPI cards) | `overview.jsx` HealthStrip | `HealthPanel.tsx` (4 boolean dots) | **Major** — design shows AUM, positions, queue, breaches, freshness %, coverage % with tone colors. Current shows simple green/red dots. |
| TriageTable (sortable recommendation list) | `overview.jsx` TriageTable | `RecommendationCard.tsx` (single card) | **Major** — design shows a multi-row table with rank, ticker, stance badge, confidence bar, sparkline, status, flags. Current shows one card. |
| RegimeStrip (regime, signal posture, sector tilt) | `overview.jsx` RegimeStrip | Not present | **New** — requires regime data from backend |
| ActivityFeed (chronological events) | `overview.jsx` ActivityFeed | Activity count text only | **Major** — design shows rich event items with icons, actors, timestamps |

### Decision Workspace (`/decision`)

| Design Element | Design Source | Current Code | Gap |
|---|---|---|---|
| HeroStrip (recommendation hero) | `hero.jsx` | Header + rationale card + StatusBadge | **Major** — design has rec ID, thesis narrative, stance/weight/horizon/delta strip, action bar. Current has basic header. |
| ConfRing (circular confidence indicators) | `hero.jsx` | `ConfidenceBlock.tsx` (horizontal bars) | **Visual** — design uses rings with numeric center. Current uses bars. Both show model/data/ops. |
| ActionBar (publish/defer/monitor) | `hero.jsx` | Not present | **New** — requires publication state machine support |
| EvidenceCard (numbered evidence items) | `modules.jsx` | Not present | **New** — requires evidence data from backend |
| RiskCard (constraint gauges with limits) | `modules.jsx` | `RiskOverlayStage.tsx` (text-only) | **Major** — design shows progress bars with limit markers and breach states |
| ChartCard (price chart with event markers) | `chart.jsx` | `WeightsBarChart.tsx` (bar chart only) | **Major** — design shows time-series with bands and markers. Different chart type. |
| ScenarioCard (what-if controls) | `scenario.jsx` | Not present | **New** — requires scenario simulation backend |
| DisagreementCard (engine disagreement summary) | `modules.jsx` | Not present | **New** — requires per-engine signal data |
| Pipeline stages (Selection/Allocation/Timing/Risk) | — | `SelectionStage.tsx` etc. | **Keep** — current stage cards are functional but not in design package. Design focuses on the hero+evidence+risk pattern instead. |

### Engine Comparison (`/comparison`)

| Design Element | Design Source | Current Code | Gap |
|---|---|---|---|
| ComparisonMatrix (engines × dimensions) | `comparison.jsx` | Side-by-side bar chart + table | **Major** — design shows a rich multi-engine matrix with per-dimension cells (stance, confidence, target, weight, horizon, risk, drivers). Current shows rec vs equal-weight only. |
| AlignmentChart (scatter bubble chart) | `comparison.jsx` | Not present | **New** — requires per-engine stance/confidence/weight data |
| MethodologyCard (engine detail on selection) | `comparison.jsx` | Not present | **New** |
| SynthesisCard (resolution guidance) | `comparison.jsx` | Rationale text card | Enhance — add synthesis rules and weighted output |

### Replay (`/replay`)

| Design Element | Design Source | Current Code | Gap |
|---|---|---|---|
| Replay timeline scrubber | iOS only | Replay list + detail cards | **Design gap** — web replay not prototyped. Current implementation is functional but plain. |
| Stage snapshot cards | — | `StageSnapshotCard` in page | Keep — works for now |

### Backtests (`/backtests`)

| Design Element | Design Source | Current Code | Gap |
|---|---|---|---|
| Not prototyped | — | Experiment list, 7 metric cards, equity curve, config table | **Design gap** — "still to design" per handoff. Current implementation is functional. |

### Paper Portfolio (`/paper`)

| Design Element | Design Source | Current Code | Gap |
|---|---|---|---|
| Not prototyped | — | Holdings table, drift chart, event log | **Design gap** — "still to design" per handoff. Current implementation is functional. |

### Admin / Ops (`/admin`)

| Design Element | Design Source | Current Code | Gap |
|---|---|---|---|
| Publication Queue | `ops.jsx` OpsQueue | Placeholder page | **Major** — full ops command center with queue, feeds, engines, breaches, incidents, audit |
| Data Feeds health | `ops.jsx` OpsFeeds | Not present | **New** |
| Engine health | `ops.jsx` OpsEngines | Not present | **New** |
| Breach watch | `ops.jsx` OpsBreaches | Not present | **New** |
| Incident investigation | `ops.jsx` OpsIncidents | Not present | **New** |
| Audit trail | `ops.jsx` OpsAudit | Not present | **New** |

### Shell / Sidebar / Context Pane

| Design Element | Design Source | Current Code | Gap |
|---|---|---|---|
| TopBar (brand, breadcrumbs, scope chips, search, notifications, avatar) | `shell.jsx` TopBar | Not present — no top bar | **Major** — current shell has sidebar only |
| LeftNav (workspaces + operations + saved views, collapsible, badges) | `shell.jsx` LeftNav | `Sidebar.tsx` (basic nav with letter icons) | **Major** — design has real icons, badge counts, saved views, operations section |
| ContextPane (tabbed: Risk/Provenance/Compare/Notes) | `context.jsx` ContextPane | `ContextPane.tsx` (single-content pane) | **Major** — design has tabbed pane with structured content per tab. Current is a generic content slot. |

---

## 4. Design Tokens Mapping

### Current State
The codebase uses Tailwind utility classes with custom `qp-*` color names defined as hex values in `tailwind.config.ts`. Light theme only.

### Design Package State
The design package uses CSS custom properties (`--canvas`, `--surface`, `--ink`, `--primary`, `--pos`, `--caution`, `--breach`) with oklch color values. Supports light+dark themes and 3 density levels.

### Integration Strategy

**Step 1:** Add CSS custom properties from `styles.css` `:root` and `[data-theme="dark"]` blocks into `frontend/src/app/globals.css`.

**Step 2:** Update `tailwind.config.ts` to reference CSS variables instead of hex values:
```ts
colors: {
  canvas: 'var(--canvas)',
  surface: 'var(--surface)',
  'surface-2': 'var(--surface-2)',
  ink: 'var(--ink)',
  'ink-2': 'var(--ink-2)',
  'ink-3': 'var(--ink-3)',
  primary: 'var(--primary)',
  pos: 'var(--pos)',
  caution: 'var(--caution)',
  breach: 'var(--breach)',
  // ... etc
}
```

**Step 3:** Migrate existing `qp-*` class references to new token names. This is a find-and-replace operation across all components.

**Step 4:** Add theme toggle (`data-theme="dark"` on `<html>`) and density toggle (`data-density`) — can be deferred.

### Token Details

| Token Group | Design Value | Current Value | Action |
|---|---|---|---|
| **Canvas** | `oklch(0.985 0.003 240)` | `#f8fafc` | Replace — very similar, design is authoritative |
| **Surface** | `oklch(1 0 0)` (white) | `#ffffff` | Same |
| **Ink (heading)** | `oklch(0.22 0.015 250)` | `#0f172a` | Replace — very similar |
| **Ink-2 (body)** | `oklch(0.42 0.012 250)` | `#475569` | Replace — similar |
| **Primary** | `oklch(0.52 0.17 255)` | `#2563eb` | Replace |
| **Pos (green)** | `oklch(0.58 0.13 155)` | `#22c55e` | Replace |
| **Caution (amber)** | `oklch(0.72 0.14 75)` | `#f59e0b` | Replace |
| **Breach (red)** | `oklch(0.58 0.18 25)` | `#ef4444` | Replace |
| **Display font** | Fraunces (serif) | Not present | Add — hero titles and KPIs only |
| **Sans font** | Inter Tight | Inter | Replace — similar but tighter |
| **Mono font** | JetBrains Mono | JetBrains Mono | Keep |
| **Radii** | 6/8/12/16px | 4/8/12px | Adjust |
| **Shadows** | 3 levels with oklch | None defined | Add |
| **Density** | compact/default/comfortable | Single density | Add — can be deferred |

---

## 5. Gap Analysis

### What the Design Package Improves
1. **Shell completeness** — TopBar with breadcrumbs, scope chips, search, notifications transforms the app from a sidebar-only tool to a professional workspace
2. **Decision workspace richness** — HeroStrip with thesis narrative, confidence rings, evidence narrative, risk gauges, scenario controls, disagreement summary. Current Decision page is functional but flat.
3. **Overview triage table** — Multi-recommendation ranked table with sparklines, stance badges, flags vs current single-card view
4. **Engine comparison depth** — Multi-engine matrix with methodology cards, alignment scatter, synthesis guidance vs current rec-vs-equal-weight bar chart
5. **Ops command center** — Full admin workspace (queue, feeds, engines, breaches, incidents, audit) vs current placeholder
6. **Token system** — Professional oklch-based tokens with dark theme support vs hex-only light theme
7. **Component vocabulary** — Cards, pills, badges, scope chips, caveat rows, tabs, key-value grids vs ad-hoc Tailwind classes

### What Current Implementation Already Has
1. Working data pipeline: seeded backend → API → frontend (12 endpoints, 13 tests)
2. All 7 routes with real data (6 real pages, 1 placeholder)
3. Right context pane infrastructure with Escape key dismiss
4. 4 chart types (weights bar, comparison bar, equity curve, drift bar)
5. Shared feedback components (PageLoading, PageError, PageEmpty)
6. Decision pipeline stage cards (selection, allocation, timing, risk overlay)
7. Replay/Backtests/Paper pages (not covered by design package)

### What Is Missing in Code But Specified in Design
1. TopBar component
2. Enhanced icon system
3. Evidence narrative cards
4. Risk constraint gauges with limits
5. Scenario controls
6. Engine disagreement card
7. Full comparison matrix
8. Ops command center modules
9. Activity feed
10. Regime/signal posture display
11. Action bar (publish/defer/monitor)

### What Requires Backend/API Support
1. **Evidence data** — EvidenceCard needs per-recommendation evidence items. Not in current schema.
2. **Per-engine signals** — ComparisonMatrix needs individual engine stances, not just composite. SignalRun/SignalOutput tables exist but are not seeded or exposed via API for multi-engine comparison.
3. **Risk constraints** — RiskCard needs individual constraint values with limits. Current risk overlay stores JSON but not in the structured format the design expects.
4. **Regime data** — RegimeStrip needs regime classification, signal posture, sector tilts. Not in current schema.
5. **Activity/audit events** — ActivityFeed needs recent events. AuditEvent table exists but is not seeded or exposed.
6. **Scenario simulation** — ScenarioCard needs a scenario API. Not implemented.
7. **Publication queue** — Ops Queue needs staged recommendations. Recommendation state machine exists but no queue endpoint.

### What Is Only Visual Polish
1. Token migration (hex → oklch CSS vars)
2. Font change (Inter → Inter Tight + Fraunces)
3. StatusBadge → StatusPill visual update
4. ConfidenceBlock bars → ConfRing circles
5. Card styling consistency
6. Shadow system
7. Dark theme support

### What Is Blocked by Missing Data
1. Scenario controls — need simulation engine
2. Engine-level comparison matrix — need per-engine seed data and API
3. Regime strip — need regime classification data
4. Activity feed — need audit event seed data

---

## 6. Recommended Implementation Sequence

### Sprint D1: Token Foundation + Shell Upgrade
**Goal:** Professional look without breaking functionality
- Port CSS custom properties from `styles.css` into `globals.css`
- Update `tailwind.config.ts` to reference CSS vars
- Add Inter Tight + Fraunces fonts
- Migrate existing `qp-*` classes to new token names across all components
- Build TopBar component (brand, breadcrumbs — skip search/notifications for now)
- Upgrade Sidebar to match LeftNav design (real icons, workspace/operations sections)
- Upgrade ContextPane to tabbed model (Risk/Provenance tabs — content can be stubbed)

### Sprint D2: Decision Workspace Enhancement
**Goal:** Upgrade Decision page to design fidelity
- Build HeroStrip (replace existing header + rationale)
- Build ConfRing (replace ConfidenceBlock bars)
- Build EvidenceCard (may need backend evidence endpoint or use rationale as fallback)
- Build RiskCard with constraint gauges
- Upgrade WeightsBarChart to match design ChartCard style
- Build DisagreementCard (stub if no per-engine data)
- Add ActionBar (publish/defer/monitor — UI only, not wired)

### Sprint D3: Overview Transformation
**Goal:** Upgrade Overview from single-card to triage workspace
- Build TriageTable (may require backend endpoint for ranked recommendations list)
- Build HealthStrip KPI cards
- Build ActivityFeed (needs audit event seeding)
- Build RegimeStrip (stub if no regime data)
- Add sparkline component

### Sprint D4: Comparison Upgrade
**Goal:** Multi-engine comparison matrix
- Build ComparisonMatrix (needs per-engine signal data from backend)
- Build AlignmentChart (scatter/bubble)
- Build MethodologyCard
- Build SynthesisCard
- Seed per-engine signal data

### Sprint D5: Ops Command Center
**Goal:** Replace Admin placeholder with real ops workspace
- Build Ops Queue module
- Build Feeds health module
- Build Engine health module
- Build Breach watch module
- Build Incident investigation module
- Build Audit trail module
- Backend: ops endpoints (queue, feeds, engines, breaches, incidents)

### Sprint D6: Polish + States + Accessibility
**Goal:** Production-grade UX
- Dark theme toggle
- Density controls
- Loading skeletons (not spinners)
- Degraded/partial/error states per design spec
- Keyboard navigation audit
- Focus ring styling
- prefers-reduced-motion / prefers-color-scheme

### Deferred
- iOS app (separate project)
- Scenario simulation (backend engine needed)
- Policy editor, Universe browser
- Onboarding, auth flows

---

## 7. Truth Section

### Verified (by reading actual files)
- All 32 files in `design/handoff-package/` exist and contain substantive content
- `styles.css` contains complete light+dark token sets with oklch values
- `HANDOFF.md` contains detailed UX principles, component inventory, data contracts, and implementation guidance
- `shell.jsx` defines TopBar and LeftNav with specific scope chips, search, breadcrumbs
- `hero.jsx` defines HeroStrip with confidence rings and action bar
- `modules.jsx` defines EvidenceCard, RiskCard, DisagreementCard
- `overview.jsx` defines TriageTable, HealthStrip, RegimeStrip, ActivityFeed
- `comparison.jsx` defines ComparisonMatrix with 5 engines and 7 dimensions
- `ops.jsx` defines queue, feeds, engines, breaches, incidents, audit modules
- `context.jsx` defines 4-tab context pane (Risk, Provenance, Compare, Notes)
- Current codebase has 33 frontend source files, 7 pages, 4 chart types
- Current `tailwind.config.ts` uses hex values, not CSS variables
- Current shell has no TopBar, basic Sidebar, single-content ContextPane

### Inferred (from reading prototypes + handoff but not visually rendering)
- The design package represents a significant visual and functional upgrade over current implementation
- The token values are perceptually similar to current hex values (both are "cool neutral + blue primary") — migration should not feel like a redesign
- The design expects per-engine signal data that exists in the DB schema (SignalRun, SignalOutput) but is not currently seeded or exposed via API
- The Ops command center is the main new workspace not covered by any current page

### Still Unclear
1. **Which Overview mode should be primary?** — Design shows a multi-recommendation triage table (institutional feel). Current system has a single published recommendation. If the product is single-user single-portfolio, the triage table may need adaptation.
2. **Scope chips in TopBar** — Regime, Horizon, Universe are hardcoded in prototype. Where does this data come from in the real system? Regime is not currently modeled.
3. **Fraunces font licensing** — Fraunces is Google Fonts (OFL), should be fine. Needs to be imported.
4. **Engine comparison depth** — Design shows 5 named engines (Momentum, Fundamentals, Narrative LLM, Risk-parity, Flow/options). Current system has no per-engine signal data seeded. Implementing the full matrix needs substantial backend+seed work.
5. **Action bar state machine** — Publish/Defer/Monitor implies a governance workflow. Current recommendation has status field but no transition endpoints.
6. **iOS priority** — Package includes 12 iOS screens. Are these relevant for current development? Assumed deferred.
