# QuantPipeline — Handoff to Claude Code

> This document hands off the **complete** QuantPipeline design prototype to Claude Code for production implementation. The prototype now covers **14 web surfaces + 18 iOS screens + a full design system project**. This doc is the single source of truth for mapping prototype → production code.
>
> **Start here:** Open `Index.html`. It is the project's front door — editorial hero, IA map, and a card linking to every surface with a short description of what it does and why it exists.
>
> **Stack recommendation (web):** React 18 + Vite + Tailwind CSS + CSS variables for the token layer. The prototype's tokens are already CSS custom properties — port them into `:root` and reference from Tailwind via `theme.extend.colors`.
>
> **Stack recommendation (iOS):** SwiftUI + iOS 17 minimum. All iOS screens use stock HIG primitives (grouped lists, `.ultraThinMaterial` bars, `NavigationSplitView` for iPad). Avoid custom navigation chrome.

---

## 0. What's in the prototype

### Web — 14 surfaces

| # | File | Purpose | Primary components |
|---|---|---|---|
| 00 | `Index.html` | Project front door — IA map, editorial intro, card catalog of every surface | `index-app.jsx`, `index-previews.jsx`, `index-page.css` |
| 01 | `Overview.html` | Morning triage hub — top recs, portfolio health, activity feed | `overview-app.jsx`, `overview.jsx`, `overview.css` |
| 02 | `Decision Workspace.html` | Single-rec deep dive — hero, evidence, scenario, disagreement | `app.jsx`, `hero.jsx`, `modules.jsx`, `chart.jsx`, `scenario.jsx`, `context.jsx` |
| 03 | `Engine Comparison.html` | Side-by-side engine votes + methodology + synthesis | `compare-app.jsx`, `comparison.jsx` |
| 04 | `Replay.html` | Time-travel forensics of a past recommendation | `replay-app.jsx`, `replay.jsx`, `replay-data.jsx`, `replay.css` |
| 05 | `Backtests.html` | Propose and validate new models before they join live engines | `backtests-app.jsx`, `backtests.jsx`, `backtests-data.jsx`, `backtests.css` |
| 06 | `Policy Editor.html` | Guardrails (position limits, concentration, VaR) with live impact preview | `policy-app.jsx`, `policy.jsx`, `policy-data.jsx`, `policy.css` |
| 07 | `Paper Portfolio.html` | Live-but-simulated P&L for published recs not yet routed to OMS | `paper-app.jsx`, `paper.jsx`, `paper-data.jsx`, `paper.css` |
| 08 | `Universe.html` | Saved universes, filters, factor exposure, versioned constituent diffs | `universe-app.jsx`, `universe.jsx`, `universe-data.jsx`, `universe.css` |
| 09 | `Ops.html` | Command center — publication queue, feed health, incidents, breaches | `ops-app.jsx`, `ops.jsx`, `ops.css` |
| 10 | `Integrations.html` | Data source catalog — connected feeds, available integrations, change log | `integrations-app.jsx`, `integrations.jsx`, `integrations-data.jsx`, `integrations.css` |
| 11 | `Onboarding.html` | 6-step first-run flow + post-onboarding team management | `onboarding-app.jsx`, `onboarding.jsx`, `onboarding-data.jsx`, `onboarding.css` |
| 12 | `States.html` | States gallery — empty, loading, error, degraded, locked | `states.css` (inline) |
| 13 | `Design System.html` | Tokens, type, icons, 60+ components with all states, motion primitives | `ds-app.jsx`, `ds-foundations.jsx`, `ds-components.jsx`, `design-system.css` |

**Shared across all web surfaces:**
- `styles.css` — global tokens + component library (**port as source of truth**)
- `tokens.css` — clean token-only export (see also `design-system.css`)
- `icons.jsx` — inline SVG icon set (~40 icons, stroke-based, Lucide-compatible names)
- `shell.jsx` — `TopBar`, `LeftNav`, `Brand`
- `context.jsx` — right-rail context pane
- `tweaks-panel.jsx` — **prototype-only**, do not port

### iOS — 18 screens

All under `ios/`. Presented on a single design canvas at `iOS App.html`.

| File | Screens |
|---|---|
| `ios-shared.jsx` | Tokens (`IOS.light` / `IOS.dark`), `IOSPhone` frame, `IOSNav`, `IOSTabBar`, SF-style icon set |
| `screens-today.jsx` | Today (2 variations: list vs. card), Alerts inbox, Watchlist |
| `screens-decision.jsx` | Decision detail (2 variations: full vs. compact), Scenario controls, Publish/Face ID sheet, Compare, Replay |
| `screens-rest.jsx` | Notes, Settings, role-scoped views |
| `screen-ipad.jsx` | iPad three-column split view |
| `design-canvas.jsx` | Presentation wrapper (prototype-only) |

---

## 1. Product framing

**QuantPipeline** is a decision-support platform for quantitative portfolio managers. It converts heterogeneous engine outputs (value, flow, news, quality) into a single recommendation a PM can **accept, challenge, or defer**.

**Non-goals:** it is not a trading terminal, not an OMS, not a market-data dashboard.

**Core UX principles** — these MUST survive implementation:

1. **Summary before detail.** Every workspace opens with "what changed and why does it matter now?" Ambient data is secondary.
2. **Progressive challenge.** Recommendation → Evidence → Disagreement → Replay is a *flow*, not tabs.
3. **Decision continuity.** Navigating between surfaces preserves `thesis`, `horizon`, `scenario`.
4. **Trust decomposition.** Model confidence, data quality, operational readiness are separate signals, always shown together (the **confidence trio**).
5. **Action accountability.** `Publish` / `Defer` / `Monitor` are explicit state transitions with audit log.
6. **Separation of duties.** Admin edits policies but cannot publish. PM publishes but cannot edit the policies that constrain them. This is enforced in the role model — see §7.

---

## 2. Information architecture

The IA is organized in four lanes. `Index.html` visualizes this directly.

### Lane 1 · Daily flow (triage → decide)
```
/overview                      — Morning triage hub
/decision/:id                  — Decision workspace (hero + evidence + scenario)
/decision/:id/compare          — Engine comparison matrix
/decision/:id/replay           — Time-travel replay of this rec's lifecycle
/paper                         — Paper P&L dashboard (live-but-simulated)
```

### Lane 2 · Model lab (propose → ship)
```
/universe                      — Universe browser (pick instruments)
/backtests                     — Propose & validate new models
/policies                      — Policy editor (guardrails with live impact)
/paper                         — (shared with Lane 1) — validation surface
```

### Lane 3 · Admin & ops (setup + run)
```
/onboarding                    — First-run flow (6 steps)
/admin/team                    — Team management (members, roles, SSO, audit)
/admin/integrations            — Data sources — connected + catalog + change log
/ops                           — Command center (queue, feeds, incidents)
```

### Lane 4 · Reference (craft)
```
/_design-system                — Internal: tokens, components, states
/_states                       — Internal: empty/loading/error gallery
```
(These are design references, not production routes. Keep them in a `--dev` build only.)

### iOS IA (read + approve-focused; publishing stays desktop-only)
```
Today       (tab) → triage + briefing + regime summary
Decisions   (tab) → open recs → Decision detail → Scenario / Compare / Replay (modals)
Compare     (tab) → engine matrix for a selected rec
Alerts      (tab) → breach / data / policy inbox
Me          (tab) → profile, team, security

Modal flows: Scenario · Publish-to-paper (Face ID) · Notes · Replay · Watchlist
```

**Shell:** three-zone on desktop (nav L · canvas C · context R), two-zone on narrow viewports. Mobile collapses context to a bottom sheet. Nav is collapsible to icons-only.

---

## 3. Design tokens

All tokens live in `styles.css` as CSS custom properties. Dark theme is the product default; light is supported via `data-theme="light"` on `<html>`.

### Color — dark theme (default)

```css
--canvas:     oklch(0.165 0.012 250);
--surface:    oklch(0.205 0.014 250);
--surface-2:  oklch(0.225 0.014 250);
--surface-3:  oklch(0.25  0.015 250);
--line:       oklch(0.3   0.013 250);
--line-strong:oklch(0.38  0.015 250);

--ink:    oklch(0.96  0.005 250);
--ink-2:  oklch(0.78  0.008 250);
--ink-3:  oklch(0.62  0.01  250);
--ink-4:  oklch(0.48  0.012 250);

--primary:          oklch(0.68 0.16 255);
--primary-ink:      oklch(0.15 0.01 250);
--primary-soft:     oklch(0.3  0.08 255);
--primary-soft-ink: oklch(0.85 0.1 255);

--pos:              oklch(0.7  0.15 155);
--pos-soft:         oklch(0.3  0.07 155);
--pos-soft-ink:     oklch(0.85 0.12 155);

--caution:          oklch(0.78 0.15 75);
--caution-soft:     oklch(0.32 0.08 75);
--caution-soft-ink: oklch(0.88 0.12 80);

--breach:           oklch(0.7  0.19 25);
--breach-soft:      oklch(0.32 0.09 25);
--breach-soft-ink:  oklch(0.88 0.14 25);

--accent:   oklch(0.7 0.12 215);     /* chart accent */
--accent-2: oklch(0.7 0.13 290);     /* chart accent 2 */
```

Light-theme values are in `styles.css` under the `:root` block (without `[data-theme]`).

### Typography

```css
--font-display: 'Fraunces', Georgia, serif;          /* hero titles, big KPIs */
--font-sans:    'Inter Tight', system-ui, sans-serif;/* body, UI */
--font-mono:    'JetBrains Mono', ui-monospace, monospace; /* numbers, IDs, tickers */
```

Three density modes — set `data-density="compact|default|comfortable"` on `<html>`. See `--dens-*` in `styles.css`.

### Radii, spacing, motion

```css
--r-sm: 4px; --r-md: 6px; --r-lg: 10px; --r-xl: 14px;
--dens-pad: 20px; --dens-gap: 14px; --dens-text: 13.5px;
```

Motion: transitions **150–220ms**. Respect `prefers-reduced-motion: reduce` — disable transitions, don't snap. No entrance animations; only state transitions (hover, focus, selected, loading).

### Token export for Tailwind

Copy `:root` + `[data-theme="dark"]` from `styles.css` into `src/styles/tokens.css`. Then in `tailwind.config.js`:

```js
theme: {
  extend: {
    colors: {
      ink: 'var(--ink)', 'ink-2': 'var(--ink-2)', 'ink-3': 'var(--ink-3)',
      surface: 'var(--surface)', 'surface-2': 'var(--surface-2)', 'surface-3': 'var(--surface-3)',
      line: 'var(--line)', 'line-strong': 'var(--line-strong)',
      primary: 'var(--primary)', 'primary-soft': 'var(--primary-soft)',
      pos: 'var(--pos)', caution: 'var(--caution)', breach: 'var(--breach)',
      accent: 'var(--accent)', 'accent-2': 'var(--accent-2)',
    },
    fontFamily: {
      display: ['Fraunces','serif'],
      sans: ['"Inter Tight"','system-ui','sans-serif'],
      mono: ['"JetBrains Mono"','ui-monospace','monospace'],
    },
    borderRadius: { sm: '4px', md: '6px', lg: '10px', xl: '14px' },
  },
},
```

---

## 4. Component inventory

Every component the production app needs. Source files are the prototype reference — class/prop contracts are stable, data is stubbed.

### Shell — used on every surface except Onboarding, Index, Design System

| Component | Source | States |
|---|---|---|
| `TopBar` | `shell.jsx` | default, nav-collapsed, no-context |
| `LeftNav` | `shell.jsx` | default, collapsed (icon-only), active item by `__PAGE` |
| `ContextPane` | `context.jsx` | tabbed (Risk / Provenance / Compare / Notes); 360px fixed desktop, bottom sheet mobile |
| `Brand` | `shell.jsx` | Anchor to `/` |

### Decision Workspace cards

| Component | Source | States required |
|---|---|---|
| `HeroStrip` | `hero.jsx` | default, fresh, provisional, stale, published, pending-review, degraded |
| **Confidence trio** | `hero.jsx` | three bars (model / data / operational) × normal · warning · breach |
| `EvidenceCard` | `modules.jsx` | populated, loading, partial (with `caveat-row`), empty |
| `RiskCard` | `modules.jsx` | all-green, warning, breach (limit marker crossed) |
| `ChartCard` | `chart.jsx` | default, no-band, hover (event marker tooltip), loading skeleton |
| `ScenarioCard` | `scenario.jsx` | idle, editing (shows **Delta preview strip** old→new), applied |
| `DisagreementCard` | `modules.jsx` | 2–8 engines; "Open matrix" navigates to Comparison |
| `ActionBar` | inline in `hero.jsx` | default, publishing, defer-modal open, disabled (permission) |

### Engine Comparison

| Component | Source |
|---|---|
| `ComparisonMatrix` | `comparison.jsx` — engines × dimensions; row click selects engine; sticky left column; synthesis row pinned with primary tint |
| `AlignmentChart` | `comparison.jsx` — scatter: X=stance, Y=confidence, bubble size=engine weight; synthesis point overlaid |
| `MethodologyCard` | `comparison.jsx` — for selected engine: "what it sees / what it ignores" + metrics + caveat |
| `SynthesisCard` | `comparison.jsx` — rules applied + weighted outputs + action bar back to Decision |

### Overview

| Component | Source |
|---|---|
| `TriageTable` | `overview.jsx` — top recs, click ticker → Decision Workspace |
| `PortfolioHealthStrip` | `overview.jsx` — regime pulse, risk metrics, breach count |
| `ActivityFeed` | `overview.jsx` — publishes, breaches, data events, mentions |
| `BriefingCard` | `overview.jsx` — AI-generated morning brief (copy placeholder) |

### Replay

| Component | Source |
|---|---|
| `ReplayScrubber` | `replay.jsx` — horizontal timeline of rec lifecycle; click any marker to load that state |
| `ReplayStatePanel` | `replay.jsx` — confidence/evidence/engines as they were at scrub position |
| `ReplayArrivedAfter` | `replay.jsx` — evidence that arrived *after* the decision was made |

### Backtests

| Component | Source |
|---|---|
| `BacktestConfigForm` | `backtests.jsx` — engine selection, universe, period, benchmarks |
| `EquityCurveChart` | `backtests.jsx` — NAV + benchmark + drawdown band |
| `BacktestMetrics` | `backtests.jsx` — Sharpe, max DD, hit rate, rolling Sharpe |
| `BacktestList` | `backtests.jsx` — saved runs with status (running / complete / failed) |

### Policy Editor

| Component | Source |
|---|---|
| `PolicyTree` | `policy.jsx` — hierarchy of rules (position / concentration / VaR / sector) |
| `PolicyEditor` | `policy.jsx` — edit any leaf; live validation |
| `ImpactPreview` | `policy.jsx` — **key innovation**: every edit shows which recs get blocked + how exposures shift *before* save |

### Paper Portfolio

| Component | Source |
|---|---|
| `PaperHeader` | `paper.jsx` — NAV, inception date, cumulative P&L |
| `PaperNAVChart` | `paper.jsx` — chart with benchmark overlay |
| `PaperPositions` | `paper.jsx` — sortable table of current positions |
| `PaperAttribution` | `paper.jsx` — engine-by-engine P&L attribution |

### Universe

| Component | Source |
|---|---|
| `UniverseList` | `universe.jsx` — saved universes sidebar |
| `ConstituentsTable` | `universe.jsx` — instruments × factors matrix with z-scores |
| `FilterRow` | `universe.jsx` — chips: min mcap, min ADV, liquidity score, sectors, scope |
| `FactorPanel` | `universe.jsx` — basket mean z-score bars + sector weights pie |
| `DiffBanner` | `universe.jsx` — pending edits vs. saved version; preview before save |

### Ops

| Component | Source |
|---|---|
| `OpsStrip` | `ops.jsx` — 4 KPIs: open incidents, queue depth, feed coverage, policy breaches |
| `ModQueue` | `ops.jsx` — publication queue with age, status |
| `ModFeeds` | `ops.jsx` — feed health with lag, coverage, SLO, pulse indicator |
| `ModEngines` | `ops.jsx` — engine status + confidence cap |
| `ModIncidents` | `ops.jsx` — open incidents with affected-rec count |
| `IncidentDrawer` | `ops.jsx` — full incident view with timeline |

### Integrations

| Component | Source |
|---|---|
| `IntegrationsHealth` | `integrations.jsx` — 4 KPIs strip |
| `ConnectedSources` | `integrations.jsx` — table with schema, auth, last sync, usage, cost |
| `AvailableCatalog` | `integrations.jsx` — connectable integrations marketplace |
| `ChangeLog` | `integrations.jsx` — audit of connect/rotate/disconnect events |

### Onboarding

| Component | Source |
|---|---|
| `StepSignIn` | `onboarding.jsx` — SSO (Okta/Entra/Google) + email fallback |
| `StepOrg` | `onboarding.jsx` — firm name, size, decision style, asset classes |
| `StepRoles` | `onboarding.jsx` — 4 roles with perm previews + full matrix toggle |
| `StepInvites` | `onboarding.jsx` — email+role rows, magic-link invite |
| `StepReview` | `onboarding.jsx` — summary with inline Edit → go-to-step |
| `StepDone` | `onboarding.jsx` — success + 3 next-action cards |
| `TeamManagement` | `onboarding.jsx` — post-onboarding admin: Members / Pending / Roles / SSO / Audit |

### Utility classes in `styles.css`

```
.card, .card-head, .card-body, .meta          — base container
.btn (+ .primary, .ghost, .sm)                — buttons
.status-pill (fresh/provisional/published/pending/stale)
.risk-pill (low/moderate/elevated/high)
.engine-stance (buy/hold/sell/trim)
.scope-chip (+ .regime variant)               — breadcrumb/filter chips
.kbd                                          — keyboard key hint
.caveat-row                                   — inline warning with icon
.tab, .tab-row                                — underline tabs
.ctx-kv                                       — 2-column key/value grid
```

---

## 5. Required states for every component

For every production component, implement and test:

1. **Default** — realistic data
2. **Loading** — skeleton or shimmer, never spinner-only
3. **Empty** — explicit copy + icon, no blank card
4. **Degraded** — partial data with `caveat-row` explaining what's missing and why
5. **Error** — recoverable with retry
6. **Permission-limited** — rendered but read-only, with clear visual indicator (see `Viewer` role in §7)

Plus interaction states: `hover`, `focus-visible`, `disabled`, `active` / `selected`.

**See `States.html`** for reference implementations on the four primary surfaces (Decision Workspace, Overview, Engine Comparison, Ops). The newer surfaces (Replay, Policy, Backtests, Paper, Universe, Onboarding, Integrations) have default states only in the prototype — they're a TODO before production.

---

## 6. Accessibility contract

- Every interactive element reachable by keyboard. Visible `:focus-visible` ring at 2px `--primary`.
- Color is never the only signal: status pills carry text, risk uses shape + color, disagreement bars have numeric labels.
- Charts: provide a data-table fallback (linked, not hidden) and ARIA descriptions for SVG figures.
- Respect `prefers-reduced-motion` and `prefers-color-scheme`.
- Minimum target 32×32 for icon buttons (desktop), 44×44 on mobile.
- Numbers in tables: right-aligned, monospace, `tabular-nums`.

---

## 7. Role model & permissions

Separation of duties is enforced. The four roles are:

| Role | Can do | Cannot do |
|---|---|---|
| **Admin** | Manage team, edit policies, manage data sources, view audit log | **Publish decisions** (separation of duties) |
| **PM** (Portfolio Manager) | Publish decisions, run scenarios, view own book | Edit the policies that constrain them, view other PMs' books |
| **Analyst / Quant** | Build models, run backtests, propose recs, edit model configs | Publish, edit policies |
| **Viewer** | View recs (weights/expected-Δ masked), portfolio health | Run scenarios, publish, see weights |

**See `Onboarding.html` step 3 and Team Management → Roles tab** for the full 11-row × 4-column permissions matrix. Port the matrix verbatim into your authorization layer (Casbin / OSO / custom — doesn't matter, but the matrix shape is the contract).

Mount permission checks at route guards AND in the component tree (double-mount). Viewer-masked fields should render placeholder dashes, not throw or hide the entire card.

---

## 8. Data contracts

Extracted from the prototype. Refine against your actual engine outputs before wiring.

```ts
type Stance = 'buy' | 'hold' | 'sell' | 'trim';
type RiskLevel = 'low' | 'moderate' | 'elevated' | 'high';
type RecStatus = 'fresh' | 'provisional' | 'published' | 'pending' | 'stale';
type Role = 'admin' | 'pm' | 'analyst' | 'viewer';

interface Recommendation {
  id: string;                  // "REC-2026-0419-NVDA-L"
  ticker: string;
  name: string;
  sector: string;
  universe: string;
  stance: Stance;
  weightPct: number;           // 0.042 = +4.2%
  horizon: '1M' | '3M' | '6M' | '1Y';
  expectedDelta: number;       // 0.048
  status: RecStatus;
  version: number;             // bumps on republish
  ageMinutes: number;
  thesis: string;              // markdown
  confidence: { model: number; data: number; operational: number };  // 0..1 each
  evidence: Array<{ id: string; text: string; delta?: Delta; caveat?: string }>;
  engines: Engine[];
  dispersion: number;          // 0..1 — disagreement score
  risk: { drawdown: number; var: number; liquidityDays: number; singleName: number };
  flags: Array<{ kind: 'breach' | 'caution' | 'info'; text: string }>;
  publishedAt?: string;
  publishedBy?: string;
}

interface Engine {
  key: string;
  name: string;                // "Momentum"
  stance: Stance;
  confidence: number;
  weight: number;              // portfolio weight from this engine
  priceTarget: number;
  weightChangeBps: number;
  horizon: string;
  risk: RiskLevel;
  drivers: string[];           // top 3
  ignores: string[];           // methodology transparency
  note: string;
  dataFreshnessMin: number;
}

interface RiskConstraint {
  key: string;
  label: string;
  value: number;
  unit: '%' | 'bps' | '$' | 'x' | 'σ';
  limit?: number;
  status: 'ok' | 'warning' | 'breach';
}

interface Scenario {
  regime: 'risk-on' | 'risk-off' | 'rotation' | 'late-cycle';
  horizonMonths: number;
  stressToggles: Record<string, boolean>;
  overrides: Record<string, number>;
}

interface Policy {
  id: string;
  kind: 'position-limit' | 'concentration' | 'var-cap' | 'sector' | 'single-name';
  scope: 'global' | 'book' | 'universe';
  params: Record<string, number>;
  hardLimit: boolean;          // vs soft (warning only)
  createdBy: string;
  version: number;
}

interface Universe {
  id: string;
  name: string;
  version: number;
  constituents: Array<{
    ticker: string;
    mcap: number;
    adv: number;
    liquidityScore: number;
    beta: number;
    factors: Record<string, number>;  // z-scores
    inBasket: boolean;
  }>;
  filters: { minMcap: number; minADV: number; liqMin: number; sectors: string[] };
}

interface Integration {
  id: string;
  name: string;                // "Bloomberg · price feed"
  status: 'connected' | 'degraded' | 'disconnected';
  schema: string;              // "prices.ohlcv.v2"
  auth: 'oauth2' | 'api-key' | 'ssh' | 'scim';
  lastSync: string;            // ISO
  usageThisMonth: number;      // requests
  costThisMonth: number;       // USD
  slo: number;                 // 0..1
}
```

---

## 9. Web stack — React + Vite + Tailwind

```bash
npm create vite@latest quantpipeline-web -- --template react-ts
cd quantpipeline-web
npm i -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm i react-router-dom@6
```

**Token port:**
1. Copy `styles.css` → `src/styles/tokens.css` (keep ALL the `:root` / `[data-theme="dark"]` blocks and utility classes verbatim).
2. Import from `main.tsx`.
3. Reference in Tailwind config (§3).

**Component port:** each prototype `*.jsx` file becomes a folder of components under `src/components/`:
```
src/components/
  Shell/       — TopBar.tsx, LeftNav.tsx, Brand.tsx, ContextPane.tsx
  Decision/    — HeroStrip.tsx, EvidenceCard.tsx, RiskCard.tsx, ...
  Compare/     — ComparisonMatrix.tsx, AlignmentChart.tsx, ...
  Overview/    — TriageTable.tsx, PortfolioHealthStrip.tsx, ...
  Replay/      — ReplayScrubber.tsx, ReplayStatePanel.tsx
  Backtests/   — ...
  Policy/      — PolicyTree.tsx, PolicyEditor.tsx, ImpactPreview.tsx
  Paper/       — ...
  Universe/    — ...
  Ops/         — ModQueue.tsx, ModFeeds.tsx, ...
  Integrations/— ...
  Onboarding/  — StepSignIn.tsx, StepOrg.tsx, ... TeamManagement.tsx
  ui/          — Btn, StatusPill, RiskPill, EngineStance, CaveatRow, Kbd
```

**Routing:** `react-router-dom` v6. One route per IA path (§2). Keep `thesis` / `horizon` / `scenario` in a `DecisionContext` that persists across `/decision/:id/*` routes.

**Data layer:** The prototype hard-codes data in `*-data.jsx` files. Replace with a typed API client (tRPC / React Query / your pattern). Data shapes in §8.

**Do NOT port:**
- `tweaks-panel.jsx`, the `useTweaks` hook, or any `EDITMODE-BEGIN/END` comment blocks — all prototype-only.
- `window.__PAGE` globals — use the active route from the router instead.
- `Object.assign(window, { ... })` cross-file sharing — convert to proper ES exports.
- `<script type="text/babel">` loading — compile JSX ahead of time with SWC (Vite default).

**DO port:**
- Every class in `styles.css` — keep class names and structure.
- Component JSX structure from the `*.jsx` files.
- Icon set from `icons.jsx` (or swap for Lucide, keeping the same names: `overview`, `decision`, `compare`, `risk`, `replay`, `backtest`, `paper`, `universe`, `news`, `ops`, `shield`, `target`, `search`, `eye`, etc.).

---

## 10. iOS stack — SwiftUI

**Target:** iOS 17+ (iPhone + iPad). Use size classes for split view: `regular` horizontal → `NavigationSplitView`, else `TabView` stacked.

**Prototype → SwiftUI mapping:**

| Prototype element | SwiftUI |
|---|---|
| Large title nav (`IOSNav`) | `.navigationTitle(…).toolbarTitleDisplayMode(.large)` |
| Grouped card list | `List { Section {} }` with `.listStyle(.insetGrouped)` |
| Tab bar (`IOSTabBar`) | `TabView` with `.tabItem` |
| Blur bottom bar (publish) | `.safeAreaInset(edge: .bottom)` + `.background(.ultraThinMaterial)` |
| Scope chip strip | Horizontal `ScrollView` of pill `Button`s |
| Primary action | `Button` + `.buttonStyle(.borderedProminent)` |
| Publish sheet (Face ID) | `.sheet(isPresented:)` + `LocalAuthentication` |
| Scenario controls | `Form` with `Slider` / `Toggle` + live delta in header |
| Replay scrubber | `Slider` bound to `selectedSnapshotIndex` |
| Mini sparkline / confidence history | Swift Charts (`LineMark` + `AreaMark`) |
| Engine bars | Swift Charts `BarMark` |

**Color tokens → `Assets.xcassets` Color Sets** (light + dark variants for each):
`ink`, `ink2`, `ink3`, `surface`, `surface2`, `surface3`, `separator`, `blue`, `green`, `red`, `orange`, `indigo`.

Prefer system colors (`Color(.label)`, `.systemBackground`) where the design matches; only override when the token diverges.

**Type:** SF Pro. Large title `.system(size: 34, weight: .bold)`, body `.system(size: 17)`, caption `.system(size: 13)`, mono metrics `.system(.caption, design: .monospaced)`.

**Permissions & state:**
- Face ID gate on **Promote to paper** using `LAContext.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics)`.
- **Publishing to live is disabled on mobile by design** — show a note directing to desktop.
- Persist last-viewed decision + scope selection in `@AppStorage`.
- Auto-lock after 2 minutes idle (user-configurable in Settings).

**Navigation:**
- iPhone: `TabView` with 5 tabs (Today / Decisions / Compare / Alerts / Me). Each tab has its own `NavigationStack`.
- iPad: `NavigationSplitView` — sidebar (tabs as list) + content list + detail. Matches `ios/screen-ipad.jsx`.

---

## 11. Backend contracts you'll need

The prototype assumes these backend capabilities — flag any gaps to your platform team:

| Capability | Why |
|---|---|
| **Rec scoring loop** | Produces `Recommendation` records every N minutes across universe |
| **Snapshot storage** | Every state mutation on a rec stored as immutable snapshot → powers Replay |
| **Evidence graph** | Each rec links to typed evidence nodes (news, filings, price, flow, factor Δ) |
| **Engine registry** | Introspectable list of engines with current weights + methodology metadata |
| **Policy engine** | Pure function: `(rec, policies) → { allowed, blockingPolicy?, warnings[] }` |
| **Audit log** | Append-only log of every publish / defer / override / policy edit / role change |
| **IdP integration** | SAML + SCIM for Okta/Entra, OIDC for Google Workspace |
| **OMS connector** | Per-tenant config; publish-to-live is gated on this being healthy |
| **Feed health daemon** | Reports lag, coverage, SLO, freshness per source — drives Ops and Integrations screens |
| **Paper-portfolio simulator** | Applies published recs to a simulated NAV with realistic costs/slippage |
| **Backtest runner** | Queued, distributed, cacheable; returns metrics + equity curve |

---

## 12. Implementation order (recommended)

1. **Tokens + shell** — `styles.css` tokens, `TopBar`, `LeftNav`, `ContextPane`. Wire to router. Dark-default + light variant working.
2. **Onboarding** — `Onboarding.html` flow (6 steps) + SSO + role model. Blocking every other screen until a user has an identity.
3. **Decision Workspace** — one card at a time: HeroStrip → EvidenceCard → RiskCard → ChartCard → ScenarioCard → DisagreementCard → ActionBar. Stub data until backend.
4. **Engine Comparison** — ComparisonMatrix → AlignmentChart → MethodologyCard → SynthesisCard. Link back to Decision.
5. **Overview** — TriageTable + PortfolioHealthStrip + ActivityFeed. Link top-rec rows to Decision.
6. **Policy Editor + Universe + Paper** — model-lab lane. Policy's `ImpactPreview` is the centerpiece; don't ship the editor without it.
7. **Backtests + Replay** — validation + forensics.
8. **Ops + Integrations + Team management** — admin lane.
9. **iOS app** — Today → Decisions → Compare → Alerts → Me, in that order.
10. **All 6 states per component** (§5). Don't skip — it's how the product survives contact with real data.
11. **Accessibility pass** — keyboard, focus rings, ARIA on charts, target sizes, reduced-motion, color-contrast AA minimum (AAA for body).
12. **Performance pass** — Lighthouse 90+. No layout shift on initial paint. Virtualize tables >200 rows.

---

## 13. Open questions for PM

1. How are engine weights allocated — fixed per strategy, dynamic per regime, or user-tuned per book?
2. SLA for data freshness before a rec auto-degrades to `stale`? (Prototype uses 60 min.)
3. Does Replay snapshot LLM traces, or just numeric inputs? (Major storage difference.)
4. Mobile — read-only in full, or do we allow paper-portfolio publishes?
5. Is there a user-settable theme preference, or does org policy set it?
6. Paper portfolio inception — does each tenant get one on onboarding, or do PMs create named portfolios ad-hoc?
7. Policy versioning — can we roll back a policy? Or is every edit forward-only with full audit?
8. Backtest cost — who pays compute? Billed to tenant, or all-you-can-eat?

---

## 14. Prototype file glossary (what you can safely ignore)

- `tweaks-panel.jsx` — runtime design tweaking, prototype-only.
- `*-app.jsx` files — thin composers that wire `useTweaks` to the component tree. In production, these become route components.
- `/*EDITMODE-BEGIN*/` blocks — marker comments for the prototype host to rewrite tweak defaults on disk. Strip.
- `window.__PAGE = "x"` — sets active nav item. Replace with router-derived active state.
- `Object.assign(window, { … })` — cross-file sharing within the prototype's Babel-in-browser setup. Replace with ES module exports.
- `handoff-package/` folder at project root — an earlier partial export; **this current doc supersedes it**.

---

## 15. Known gaps before production

These are designed but not yet fully states-passed — they have `default` only in the prototype:

- Replay · Policy Editor · Backtests · Paper Portfolio · Universe · Onboarding · Integrations — need empty/loading/error/degraded/locked states.
- Keyboard shortcuts overlay (⌘K command palette exists in the design but has no UI yet).
- Notifications center (bell icon in TopBar is live; drawer is TODO).
- Decision history / journal (outcome tracking 30/90d after publish).
- Per-user settings page (theme, shortcuts, defaults, auto-lock).
- Mobile Ops view (iOS currently has Today + Decision + supporting modals; no Ops-light).

Ping the designer before shipping any of these — same system, new screens.

---

*This document supersedes all prior HANDOFF versions. Last updated: deck v14, April 2026.*
