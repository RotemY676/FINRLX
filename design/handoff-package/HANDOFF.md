# QuantPipeline — Handoff to Claude Code

> This document hands off the QuantPipeline design prototype (Overview + Decision Workspace + Engine Comparison + iOS app) to Claude Code for implementation in your production codebases.
>
> **Stack recommendation (web):** React 18 + Vite + Tailwind CSS + CSS variables for the token layer. The prototype already uses CSS variables; port them into `:root` and reference from Tailwind via `theme.extend.colors`.
>
> **Stack recommendation (iOS):** SwiftUI + iOS 17+ minimum. All iOS screens map to standard HIG patterns (grouped lists, `.blur(.ultraThinMaterial)` bars, `Form` / `List` sections). Avoid custom navigation chrome.
>
> **Prototype files in this project** — everything you need to reference:
>
> **Web**
> - `Overview.html` (morning triage hub) → `overview-app.jsx` + `overview.jsx` + `overview.css`
> - `Decision Workspace.html` → `app.jsx` + `shell.jsx` · `hero.jsx` · `modules.jsx` · `chart.jsx` · `scenario.jsx` · `context.jsx`
> - `Engine Comparison.html` → `compare-app.jsx` + `comparison.jsx`
> - `styles.css` (full design tokens + component styles — shared across all pages)
> - `icons.jsx` (inline SVG icons)
> - `tweaks-panel.jsx` (runtime design-tweak panel — **prototype-only**, do not port)
>
> **iOS**
> - `iOS App.html` → design canvas wrapper; individual screens live in `ios/screens-*.jsx` + `ios/screen-ipad.jsx`
> - `ios/ios-shared.jsx` — tokens (`IOS.light` / `IOS.dark`), `IOSPhone`, `IOSNav`, `IOSTabBar`, SF-style icon set
> - 12 screens total: Today (2 variations), Decision detail (2 variations), Scenario, Publish/Face ID sheet, Alerts, Compare, Replay, Watchlist, Notes, Settings, iPad split view

---

## 1. Product framing

**QuantPipeline** is a decision‑support platform for portfolio management. It is not a trading terminal. It is a *challenge surface* that converts heterogeneous engine outputs into a single recommendation an analyst can **accept, challenge, or defer**.

Core UX principles (these MUST survive implementation):

1. **Summary before detail.** Every workspace opens with the answer to "what changed and why does it matter now?" Ambient data is secondary.
2. **Progressive challenge.** Recommendation → Evidence → Disagreement → Replay is a flow, not tabs.
3. **Decision continuity.** Navigating between screens preserves `thesis`, `horizon`, `scenario`.
4. **Trust decomposition.** Model confidence, data quality, operational readiness are separate signals, always shown together (the **confidence trio**).
5. **Action accountability.** `Publish` / `Defer` / `Monitor` are explicit state transitions.

---

## 2. Information architecture

```
/overview                      — Morning triage hub         ← IMPLEMENTED
/decision/:id                  — Decision workspace         ← IMPLEMENTED
/decision/:id/compare          — Engine comparison          ← IMPLEMENTED
/replay/:snapshotId            — time-travel replay         (iOS only so far)
/backtests                     — saved backtests
/paper                         — paper portfolio
/ops/queue                     — publication queue
/ops/health                    — data-source health
/ops/incidents                 — incident investigation
```

**iOS IA (mirrors web, read+approve focused, publishing is desktop-only):**
```
Today (tab)               → triage + briefing banner + regime summary
Decisions (tab)           → list of open recs → Decision detail
Compare (tab)             → engine matrix for a selected rec
Alerts (tab)              → breach / data / policy inbox
Me (tab)                  → profile, team, security (Face ID for promote)

Modal flows:
  Scenario controls       → slide up from decision detail
  Publish/promote sheet   → Face ID confirmation, paper-only on mobile
  Notes / annotations     → attached to decision
  Replay                  → time-travel viewer
  Watchlist & saved views → from Decisions tab
```

**Shell** — three‑zone on desktop (nav L · canvas C · context R), two‑zone on narrow. Mobile collapses context to a bottom sheet. Nav is collapsible to icons‑only.

---

## 3. Design tokens

All tokens are CSS custom properties defined in `styles.css`. **Port these verbatim into your design‑token layer** (e.g. a `tokens.css`, Tailwind `theme`, or CSS‑in‑JS theme object). Dark is the default.

### Color — dark theme (default)

```css
--canvas:     oklch(0.165 0.012 250);  /* page background */
--surface:    oklch(0.205 0.014 250);  /* cards */
--surface-2:  oklch(0.225 0.014 250);  /* recessed */
--surface-3:  oklch(0.25  0.015 250);  /* chips, hover */
--line:       oklch(0.3   0.013 250);
--line-strong:oklch(0.38  0.015 250);

--ink:        oklch(0.96  0.005 250);  /* headings, numbers */
--ink-2:      oklch(0.78  0.008 250);  /* body */
--ink-3:      oklch(0.62  0.01  250);  /* labels, meta */
--ink-4:      oklch(0.48  0.012 250);  /* axis ticks, hints */

--primary:       oklch(0.68 0.16 255); /* blue — primary action */
--primary-ink:   oklch(0.15 0.01 250);
--primary-soft:  oklch(0.3  0.08 255);
--primary-soft-ink: oklch(0.85 0.1 255);

--pos:       oklch(0.7  0.15 155);     /* measured green */
--pos-soft:  oklch(0.3  0.07 155);
--pos-soft-ink: oklch(0.85 0.12 155);

--caution:   oklch(0.78 0.15 75);      /* amber */
--caution-soft: oklch(0.32 0.08 75);
--caution-soft-ink: oklch(0.88 0.12 80);

--breach:    oklch(0.7  0.19 25);      /* red */
--breach-soft: oklch(0.32 0.09 25);
--breach-soft-ink: oklch(0.88 0.14 25);

--accent:    oklch(0.7 0.12 215);      /* cyan accent, chart only */
```

### Color — light theme

Full light‑theme tokens are in `styles.css` under `:root { ... }` (without `[data-theme]`). Swap with `document.documentElement.setAttribute('data-theme', 'light' | 'dark')`.

### Typography

```css
--font-display: 'Fraunces', Georgia, serif;        /* hero title, KPIs only */
--font-sans:    'Inter Tight', system-ui, sans-serif;  /* body, UI */
--font-mono:    'JetBrains Mono', ui-monospace, monospace; /* numbers, IDs */
```

Sizing scale (see `--dens-*` custom props in `styles.css`). Three densities: `compact` / `default` / `comfortable` — set via `data-density` on `<html>`.

### Radii / spacing

```css
--r-sm: 4px; --r-md: 6px; --r-lg: 10px; --r-xl: 14px;
--dens-pad: 20px;   /* default density */
--dens-gap: 14px;
--dens-text: 13.5px;
```

### Motion

- All transitions **150–220ms**.
- Respect `prefers-reduced-motion: reduce` — disable transitions, not instant‑on.
- No "fancy" entrance animations; only state transitions (hover, focus, selected, loading).

---

## 4. Component inventory

Each entry lists: source file in prototype · purpose · required states · notes.

### Shell (`shell.jsx`)

| Component | States | Notes |
|---|---|---|
| `TopBar` | default, nav‑collapsed, no‑context | Sticky. Contains brand, breadcrumbs, **scope chips** (regime/horizon/universe), search with ⌘K, notifications, avatar. |
| `LeftNav` | default, collapsed (icon‑only), active item | Items use real anchors (SPA router in prod). Badge counts reflect live queues. |
| `ContextPane` (`context.jsx`) | tabbed (Risk / Provenance / Compare / Notes) | 360px fixed on desktop; bottom sheet on mobile. Content rebuilds per decision scope. |

### Decision Workspace (`app.jsx` + subcomponents)

| Component | Source | States required |
|---|---|---|
| **HeroStrip** (recommendation card) | `hero.jsx` | default, fresh, provisional, stale, published, pending‑review, degraded |
| **Confidence trio** | `hero.jsx` | Three bars: model / data / operational. Each: normal, warning, breach |
| **EvidenceCard** | `modules.jsx` | populated, loading, partial (with `caveat-row`), empty |
| **RiskCard** | `modules.jsx` | all‑green, warning, breach (limit marker crossed) |
| **ChartCard** | `chart.jsx` | default, no‑band, hover (event marker tooltip), loading skeleton |
| **ScenarioCard** | `scenario.jsx` | idle, editing (shows **Delta preview strip** with old→new values), applied |
| **DisagreementCard** | `modules.jsx` | 2–8 engines; "Open matrix" navigates to Comparison |
| **ActionBar** | inline in `hero.jsx` | default, publishing, defer‑modal open, disabled (permission) |

### Engine Comparison (`comparison.jsx` + `compare-app.jsx`)

| Component | Purpose |
|---|---|
| **ComparisonMatrix** | Engines × dimensions table. Row click selects engine (drives MethodologyCard). Sticky left column, scrollable horizontally. Synthesis row pinned at bottom with primary tint. |
| **AlignmentChart** | Scatter: X = stance (sell/hold/buy), Y = confidence, bubble size = engine weight. Synthesis point overlaid. |
| **MethodologyCard** | For selected engine: "what it sees" vs "what it ignores" + key metrics + caveat. |
| **SynthesisCard** | Resolution guidance: rules applied + weighted outputs + action bar back to Decision. |

### Utility components in `styles.css`

- `.card` (+ `.card-head`, `.card-body`, `.meta`) — base container
- `.btn` — variants: `primary` | `ghost` | `sm`; all support icon + text
- `.status-pill` — `fresh` | `provisional` | `published` | `pending`
- `.risk-pill` — `low` | `moderate` | `elevated` | `high`
- `.engine-stance` — `buy` | `hold` | `sell`
- `.scope-chip` — with optional colored dot and `regime` variant
- `.kbd` — keyboard key hint
- `.caveat-row` — inline warning/info with icon
- `.tab` + `.tab-row` — underline tabs
- `.ctx-kv` — 2‑column key/value grid

---

## 5. Required states for every component

For every production component, implement and test:

1. **Default** — populated with realistic data
2. **Loading** — skeleton or shimmer, never spinner‑only
3. **Empty** — explicit copy, no blank card
4. **Degraded** — partial data with `caveat-row` explaining what's missing and why
5. **Error** — recoverable error state with retry
6. **Permission‑limited** — shown but read‑only, with clear indicator

Plus: `hover`, `focus-visible`, `disabled`, `active`/`selected`.

---

## 6. Accessibility contract

- All interactive elements reachable by keyboard. Visible `:focus-visible` ring at 2px `--primary`.
- Color is never the only signal: status pills carry text, risk uses shape + color, disagreement bars have numeric labels.
- Charts: provide a data‑table fallback (linked, not hidden) and ARIA descriptions for SVG figures.
- Respect `prefers-reduced-motion` and `prefers-color-scheme` (default dark if user has no preference).
- Minimum target size 32×32 for icon buttons, 44×44 on mobile.

---

## 7. Implementation notes for Claude Code

### What to port directly
- **Design tokens** (section 3) — verbatim.
- **All `styles.css` component classes** — copy as source of truth, or translate to your styling system (Tailwind / CSS Modules / vanilla‑extract) preserving the **exact token references** and class structure.
- **Icon set** (`icons.jsx`) — these are stroke‑only Lucide‑style SVGs; swap for Lucide if you already depend on it, but keep the same names (`overview`, `decision`, `compare`, `risk`, `replay`, etc.).

### What to reshape for production
- **Components** are written as plain JSX with inline `Object.assign(window, { ... })` for cross‑file sharing (prototype constraint). In production, convert each to a proper module export (`export { HeroStrip }`). File‑to‑component mapping is 1‑to‑many on purpose — preserve the grouping.
- **Data shape** — every component currently receives hard‑coded data. The props contract each component needs is listed in `docs/prop-contracts.md` (generate this from the prototype by reading each component's rendered values — see section 8 below).
- **Routing** — anchors in the prototype (`href="Engine Comparison.html"`) become real route transitions. Preserve the back‑link on Comparison → Decision.

### What NOT to port
- **`tweaks-panel.jsx`** — this is prototype‑only UI (runtime design tweaking). Delete.
- **`<script type="text/babel">` loading** — compile JSX ahead of time.
- **Inline `EDITMODE-BEGIN` / `EDITMODE-END` blocks in `app.jsx` and `compare-app.jsx`** — also prototype‑only.

### Drop‑in plan (recommended order)
1. Port tokens + base CSS reset + typography.
2. Port shell: `TopBar`, `LeftNav`, `ContextPane`. Wire to router.
3. Port Decision Workspace components one card at a time: `HeroStrip` → `EvidenceCard` → `RiskCard` → `ChartCard` → `ScenarioCard` → `DisagreementCard`. Stub data until backend is wired.
4. Port Engine Comparison: `ComparisonMatrix` → `AlignmentChart` → `MethodologyCard` → `SynthesisCard`.
5. Wire real data via your API layer. Implement all 6 states per component (section 5).
6. Add `prefers-reduced-motion` and `prefers-color-scheme` handling.
7. Lighthouse pass: contrast AA minimum (AAA for body text), no layout shift, 100% keyboard nav.

---

## 8. Data contracts (first pass)

Extracted from the prototype. Refine against your actual engine outputs.

```ts
type Stance = 'buy' | 'hold' | 'sell';
type RiskLevel = 'low' | 'moderate' | 'elevated' | 'high';
type RecStatus = 'fresh' | 'provisional' | 'published' | 'pending' | 'stale';

interface Recommendation {
  id: string;               // e.g. "REC-2026-0419-NVDA-L"
  ticker: string;
  company: string;
  sector: string;
  universe: string;
  stance: Stance;
  weightPct: number;
  horizon: '1M' | '3M' | '6M' | '1Y';
  expectedDelta: number;    // e.g. +0.048
  status: RecStatus;
  freshnessMin: number;     // minutes since last re-score
  thesis: string;           // markdown-capable
  confidence: {
    model: number;          // 0..1
    data: number;           // 0..1
    operational: number;    // 0..1
  };
  caveats: string[];
  publishedVersion?: number;
}

interface Evidence {
  id: string;
  order: number;
  title: string;
  body: string;
  delta?: { label: string; from: string; to: string; direction: 'pos' | 'neg' | 'neutral' };
  caveat?: string;
}

interface RiskConstraint {
  key: string;
  label: string;
  value: number;
  unit: '%' | 'bps' | '$' | 'x' | 'σ';
  limit?: number;
  status: 'ok' | 'warning' | 'breach';
}

interface Engine {
  key: string;              // "momentum"
  name: string;             // "Momentum"
  stance: Stance;
  confidence: number;       // 0..1
  weight: number;           // 0..1, portfolio weight from this engine
  priceTarget: number;
  weightChangeBps: number;  // e.g. +480 bps
  horizon: string;
  risk: RiskLevel;
  drivers: string[];        // top 3
  ignores: string[];        // methodology transparency
  note: string;             // caveat or down-weight reason
  dataFreshnessMin: number;
}

interface Scenario {
  regime: 'risk-on' | 'risk-off' | 'rotation' | 'late-cycle';
  horizonMonths: number;
  stressToggles: Record<string, boolean>;
  overrides: Record<string, number>;
}
```

---

## 9. Open questions to flag to PM

Design decisions that need product input before coding:

1. How are engine weights allocated — fixed per strategy, dynamic per regime, or user‑tuned?
2. Who can `Publish`? Role model needed.
3. What is the SLA for data freshness before a rec auto‑degrades to `stale`?
4. Does Replay snapshot everything (including LLM traces), or just numeric inputs?
5. Mobile — is it read‑only, or do portfolio managers take actions on mobile?
6. Is there a dark/light user preference, or does org policy set it?

---

## 10. Out of scope for this handoff

The prototype now covers **Overview · Decision Workspace · Engine Comparison · full iOS app (12 screens)**. Still to design:

- Admin / Ops command center (publication queue, data-source health, incidents)
- Replay timeline (web — exists on iOS)
- Policy editor
- Universe browser
- Backtests detail
- Paper portfolio dashboard

Ping the designer before shipping those — same system, new screens.

---

## 11. Web stack — React + Vite + Tailwind

**Scaffold:**
```
npm create vite@latest quantpipeline-web -- --template react-ts
cd quantpipeline-web
npm i -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**Tokens → Tailwind config.** Copy the `:root` / `[data-theme="dark"]` blocks from `styles.css` into `src/styles/tokens.css` and import from `main.tsx`. Then reference tokens in `tailwind.config.js`:
```js
theme: {
  extend: {
    colors: {
      ink: 'var(--ink)', 'ink-2': 'var(--ink-2)', 'ink-3': 'var(--ink-3)',
      surface: 'var(--surface)', 'surface-2': 'var(--surface-2)',
      line: 'var(--line)', primary: 'var(--primary)',
      pos: 'var(--pos)', caution: 'var(--caution)', breach: 'var(--breach)',
    },
    fontFamily: {
      display: ['Fraunces','serif'],
      sans: ['"Inter Tight"','system-ui','sans-serif'],
      mono: ['"JetBrains Mono"','ui-monospace','monospace'],
    },
  },
},
```

**Routing:** `react-router-dom` v6. One route per IA path. Keep `thesis` / `horizon` / `scenario` in a `DecisionContext` that persists across `/decision/:id/*` routes.

**Do NOT port:** `tweaks-panel.jsx`, `app.jsx`'s `useTweaks` hook, or the `EDITMODE-BEGIN/END` comment blocks. Those are prototype-only.

**DO port:** everything in `styles.css`, all component structure from `hero.jsx` / `modules.jsx` / `comparison.jsx` / `overview.jsx`. Break each into its own `.tsx` file under `src/components/`.

---

## 12. iOS stack — SwiftUI

**Target:** iOS 17+ (iPhone + iPad). Use size classes for the split view (`regular` horizontal size class → `NavigationSplitView`, else stacked).

**Mapping prototype → SwiftUI primitives:**

| Prototype element                          | SwiftUI                               |
|--------------------------------------------|---------------------------------------|
| Large title nav (`IOSNav`)                 | `.navigationTitle` + `.large` display |
| Grouped list card (`Group` + `Row`)        | `List { Section {} }` with `.insetGrouped` |
| Tab bar (`IOSTabBar`)                      | `TabView` with `.tabItem`             |
| Blur bottom bar (publish actions)          | `.safeAreaInset(edge: .bottom)` + `.background(.ultraThinMaterial)` |
| Scope chip strip (`Today · A`)             | Horizontal `ScrollView` of `Button` pills |
| Pull-to-action buttons                     | `Button` with `.buttonStyle(.borderedProminent)` |
| Publish sheet (Face ID)                    | `.sheet(isPresented:)` + `LocalAuthentication` framework |
| Scenario controls                          | `Form` with `Slider` / `Toggle` + live delta preview in header |
| Replay scrubber                            | `Slider` bound to `selectedSnapshotIndex` |
| Mini sparkline / confidence history        | Swift Charts (`LineMark` + `AreaMark`) |
| Engine bars                                | Custom `GeometryReader` or Swift Charts `BarMark` |

**Color tokens (add to `Assets.xcassets` as Color Sets with light + dark variants):**
- `ink`, `ink2`, `ink3`, `surface`, `surface2`, `surface3`, `separator`
- `blue` (primary · matches systemBlue), `green`, `red`, `orange`, `indigo`
- Use `Color("ink")` etc. throughout. Prefer system colors (`Color(.label)`, `.systemBackground`) for auto-dark; only override when the design diverges.

**Type:** SF Pro by default (`.system(...)`). Large titles `.system(size: 34, weight: .bold)`; body `.system(size: 17)`; captions `.system(size: 13)`; mono metrics `.system(.caption, design: .monospaced)`.

**Permissions & state:**
- Face ID gate on **Promote to paper** using `LAContext.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics)`. Publishing to live is **disabled on mobile by design** — show a note, direct to desktop.
- Persist last-viewed decision + scope chip selection in `@AppStorage`.
- Auto-lock after 2 minutes of inactivity (user-configurable in Settings).

**Navigation:**
- iPhone: `TabView` with 5 tabs (Today · Decisions · Compare · Alerts · Me). Each tab has its own `NavigationStack`.
- iPad: `NavigationSplitView` — sidebar (same tabs as a sidebar list) + content list + detail. Matches `ios/screen-ipad.jsx` three-column layout.

---

## 13. Shared contracts (web ↔ iOS)

Both clients consume the same API. Canonical recommendation shape:

```ts
type Recommendation = {
  id: string;                  // "REC-2026-0419-NVDA-L"
  ticker: string;
  name: string;
  stance: "buy" | "sell" | "trim" | "hold";
  status: "fresh" | "provisional" | "published" | "pending" | "stale";
  version: number;
  ageMinutes: number;
  horizon: "1M" | "3M" | "6M" | "12M";
  proposedWeight: number;      // 0.042 = +4.2%
  expectedDelta: number;       // 0.048
  confidence: { model: number; data: number; operational: number };
  thesis: string;              // narrative
  evidence: Array<{ text: string; caveat?: boolean }>;
  engines: Array<{
    name: string; weight: number;
    stance: "LONG"|"SHORT"|"HOLD"|"TRIM";
    confidence: number;
    rationale?: string;
  }>;
  dispersion: number;          // 0.37
  risk: { drawdown: number; var: number; liquidityDays: number; singleName: number };
  flags: Array<{ kind: "breach"|"caution"|"info"; text: string }>;
};
```

The **confidence trio** is non-negotiable on both platforms — always render all three scores, never collapse into a single number.
