# QuantPipeline — Handoff to Claude Code

> Hands off the **QuantPipeline** prototype (web + iOS) to Claude Code for production implementation.
>
> **Stack (web):** React 18 + Vite + TypeScript + Tailwind + CSS variables (token layer).
> **Stack (iOS):** SwiftUI, iOS 17+.
>
> Dark theme is the default. Light theme is supported via `data-theme="light"` on `<html>`.

---

## 0. What's in this package

### Web workspaces (all implemented)

| File | Workspace | Purpose |
|---|---|---|
| `Overview.html` | Morning triage hub | Health strip, ranked triage table, activity feed, regime strip |
| `Decision Workspace.html` | Single‑recommendation deep dive | HeroStrip + confidence trio, evidence, risk, chart, scenario, disagreement |
| `Engine Comparison.html` | Engine‑level disagreement matrix | Matrix + alignment scatter + methodology + synthesis |
| `Replay.html` | Time‑travel forensics | Scrubber timeline + engine state diff + price chart + event log + counterfactual |
| `Policy Editor.html` | Risk & policy rules | Rule list + editor form + simulation + violation log |
| `Ops.html` | Ops command center | Queue + data‑source health + incidents |
| `Backtests.html` | Saved backtests | Runs list + equity curve + drawdown + tear sheet + blotter + compare strip |
| `States.html` | Component state reference | All 6 canonical states × all Tier 1 components |
| `Design System.html` | Foundations + component library | Tokens, type, color, spacing, all components |
| `iOS App.html` | Mobile companion (12 screens) | Read + approve focused; publish is desktop‑only |

### File mapping (what to read per workspace)

| Workspace | App | Components | Styles |
|---|---|---|---|
| Overview | `overview-app.jsx` | `overview.jsx`, `shell.jsx`, `context.jsx` | `styles.css`, `overview.css` |
| Decision | `app.jsx` | `hero.jsx`, `modules.jsx`, `chart.jsx`, `scenario.jsx`, `shell.jsx`, `context.jsx` | `styles.css` |
| Comparison | `compare-app.jsx` | `comparison.jsx` | `styles.css` |
| Replay | `replay-app.jsx` | `replay.jsx`, `replay-data.jsx` | `styles.css`, `replay.css` |
| Policy | `policy-app.jsx` | `policy.jsx`, `policy-data.jsx` | `styles.css`, `policy.css` |
| Ops | `ops-app.jsx` | `ops.jsx` | `styles.css`, `ops.css` |
| Backtests | `backtests-app.jsx` | `backtests.jsx`, `backtests-data.jsx` | `styles.css`, `backtests.css` |
| States | `—` (static HTML in page) | `—` | `styles.css`, `states.css` |
| Design System | `ds-app.jsx` | `ds-foundations.jsx`, `ds-components.jsx` | `styles.css`, `design-system.css`, `tokens.css` |
| iOS | `—` | `ios/screens-*.jsx`, `ios/screen-ipad.jsx`, `ios/ios-shared.jsx` | inline in each screen |

### Shared across all workspaces

- `styles.css` — **full design system**: tokens, reset, typography, buttons, cards, pills, tables, forms, nav/shell, context pane. **Single source of truth.**
- `tokens.css` — standalone token file (subset of `styles.css` `:root`), easier to lift into Tailwind.
- `icons.jsx` — stroke‑only line icon set (≈40 glyphs, Lucide‑style).
- `shell.jsx` — `TopBar`, `LeftNav`.
- `context.jsx` — `ContextPane` (right‑side tabs).
- `tweaks-panel.jsx` — **PROTOTYPE ONLY.** Do not port.

---

## 1. Product framing

**QuantPipeline** is a decision‑support platform for portfolio management — *not* a trading terminal. It is a **challenge surface** that converts heterogeneous engine outputs into a single recommendation an analyst can `Accept`, `Challenge`, or `Defer`.

**UX principles (MUST survive implementation):**

1. **Summary before detail.** Every workspace opens with "what changed, why it matters now." Ambient data is secondary.
2. **Progressive challenge.** Recommendation → Evidence → Disagreement → Replay is a *flow*, not tabs.
3. **Decision continuity.** `thesis`, `horizon`, `scenario` persist across navigation.
4. **Trust decomposition.** Model confidence, data quality, operational readiness are **three separate signals**, always shown together (the **confidence trio**). Never collapse into one number.
5. **Action accountability.** `Publish`, `Defer`, `Monitor` are explicit state transitions with audit trails.

---

## 2. Information architecture

```
/overview                      — morning triage hub             ✓
/decision/:id                  — decision workspace             ✓
/decision/:id/compare          — engine comparison              ✓
/replay/:snapshotId            — time-travel forensics          ✓ (web + iOS)
/policy                        — risk & policy editor           ✓
/backtests                     — saved backtests                ✓
/paper                         — paper portfolio                ○ (next)
/ops/queue                     — publication queue              ✓
/ops/health                    — data-source health             ✓
/ops/incidents                 — incident investigation         ✓
/universe                      — universe browser               ○ (later)
/settings/team                 — team & permissions             ○ (later)
```

**Shell** — three‑zone on desktop (nav L · canvas C · context R), two‑zone on narrow. Mobile collapses context to a bottom sheet. Nav is collapsible to icons‑only. `data-density` on `<html>` switches `compact` | `default` | `comfortable`.

---

## 3. Design tokens

All tokens are CSS custom properties in `styles.css` (also extracted standalone to `tokens.css`). **Port verbatim.**

### Dark theme (default)
```css
--canvas:     oklch(0.165 0.012 250);
--surface:    oklch(0.205 0.014 250);
--surface-2:  oklch(0.225 0.014 250);
--surface-3:  oklch(0.25  0.015 250);
--line:       oklch(0.3   0.013 250);
--line-strong:oklch(0.38  0.015 250);

--ink:   oklch(0.96 0.005 250);  /* headings, numbers */
--ink-2: oklch(0.78 0.008 250);  /* body */
--ink-3: oklch(0.62 0.01  250);  /* labels, meta */
--ink-4: oklch(0.48 0.012 250);  /* axis ticks, hints */

--primary:      oklch(0.68 0.16 255);
--primary-soft: oklch(0.3  0.08 255);
--primary-soft-ink: oklch(0.85 0.1 255);

--pos:        oklch(0.7  0.15 155);
--pos-soft:   oklch(0.3  0.07 155);
--caution:    oklch(0.78 0.15 75);
--caution-soft:oklch(0.32 0.08 75);
--breach:     oklch(0.7  0.19 25);
--breach-soft:oklch(0.32 0.09 25);
--accent:     oklch(0.7 0.12 215);   /* charts only */
--accent-2:   oklch(0.72 0.14 300);  /* charts only */
```

Light theme lives in `:root` (default block in `styles.css`); dark override is under `[data-theme="dark"]`.

### Typography
```css
--font-display: 'Fraunces', Georgia, serif;          /* hero titles, KPIs */
--font-sans:    'Inter Tight', system-ui, sans-serif; /* body, UI */
--font-mono:    'JetBrains Mono', ui-monospace, monospace; /* numbers, IDs, tickers */
```

### Radii / spacing
```css
--r-sm: 4px; --r-md: 6px; --r-lg: 10px; --r-xl: 14px;
--dens-pad: 20px; --dens-gap: 14px; --dens-text: 13.5px;
```

### Motion
- Transitions **120–220ms**.
- Respect `prefers-reduced-motion: reduce`.
- No entrance animations, only state transitions.

---

## 4. Component inventory

See **`Design System.html`** for the live reference. See **`States.html`** for the canonical 6 states × all Tier 1 components.

### Shell
| Component | File | States |
|---|---|---|
| `TopBar` | `shell.jsx` | default, nav‑collapsed, no‑context |
| `LeftNav` | `shell.jsx` | default, collapsed (icon‑only), active item |
| `ContextPane` | `context.jsx` | tabs: Risk · Provenance · Compare · Notes |

### Decision workspace
| Component | File | States |
|---|---|---|
| `HeroStrip` (recommendation card) | `hero.jsx` | default, fresh, provisional, stale, published, pending‑review, degraded, permission‑limited |
| `ConfidenceTrio` | `hero.jsx` | normal, warning, breach (per bar) |
| `EvidenceCard` | `modules.jsx` | populated, loading, partial (`caveat-row`), empty |
| `RiskCard` | `modules.jsx` | all‑green, warning, breach |
| `ChartCard` | `chart.jsx` | default, no‑band, hover, loading skeleton |
| `ScenarioCard` | `scenario.jsx` | idle, editing (delta preview), applied |
| `DisagreementCard` | `modules.jsx` | 2–8 engines; "Open matrix" → Comparison |
| `ActionBar` | `hero.jsx` | default, publishing, defer‑modal open, disabled (permission) |

### Engine comparison
| Component | Purpose |
|---|---|
| `ComparisonMatrix` | Engines × dimensions table. Sticky left column. Synthesis row pinned at bottom. |
| `AlignmentChart` | X=stance, Y=confidence, bubble=weight. Synthesis point overlaid. |
| `MethodologyCard` | "What it sees" vs "what it ignores" + caveat. |
| `SynthesisCard` | Resolution rules + weighted outputs + action bar back to Decision. |

### Replay
| Component | File | Purpose |
|---|---|---|
| `ReplayHeader` | `replay.jsx` | Case crumb + entry/cursor price + P&L |
| `Scrubber` | `replay.jsx` | Timeline with event markers, play/pause, 0.5×/1×/2× speed |
| `EnginePanel` | `replay.jsx` | Engine state diff at cursor vs previous event |
| `ChartPanel` | `replay.jsx` | Price curve with confidence band + event markers |
| `LogPanel` | `replay.jsx` | Click‑to‑jump event log |
| `CounterfactualFooter` | `replay.jsx` | "What if we had deferred?" alt outcome |

### Policy editor
| Component | File | Purpose |
|---|---|---|
| `RuleList` | `policy.jsx` | Sortable list of rules, grouped by category, with enable toggle |
| `RuleEditor` | `policy.jsx` | Form: threshold, severity, scope, simulation preview |
| `ViolationLog` | `policy.jsx` | Recent violations with drill‑in to the offending decision |

### Ops
| Component | File | Purpose |
|---|---|---|
| `PublicationQueue` | `ops.jsx` | Pending publishes, Face‑ID gate on promote |
| `HealthStrip` | `ops.jsx` (+ `overview.jsx`) | Data‑source freshness & latency, sparklines |
| `IncidentList` | `ops.jsx` | Open incidents, assignee, severity, linked decisions |

### Backtests
| Component | File | Purpose |
|---|---|---|
| `StrategyBar` | `backtests.jsx` | Run name, status, universe, rebal, costs, Re‑run |
| `RunsList` | `backtests.jsx` | Recent + archived runs, click to activate |
| `BtMain` | `backtests.jsx` | Hero stats + equity curve + drawdown + tear sheet |
| `TradeBlotter` | `backtests.jsx` | Last N fills with P&L and hold days |
| `CompareStrip` | `backtests.jsx` | Multi‑run compare shelf, Promote to paper gate |

### Utility classes (in `styles.css`)
`.card`, `.card-head`, `.card-body`, `.meta`, `.btn` (+ `primary` | `ghost` | `sm`), `.status-pill`, `.risk-pill`, `.engine-stance`, `.scope-chip`, `.kbd`, `.caveat-row`, `.tab-row` + `.tab`, `.ctx-kv`.

---

## 5. Required states (every production component)

1. **Default** — realistic data
2. **Loading** — skeleton/shimmer, **never spinner‑only**
3. **Empty** — explicit copy, no blank card
4. **Degraded** — partial data + `caveat-row` explaining what's missing
5. **Error** — recoverable, with retry
6. **Permission‑limited** — read‑only with clear indicator (hides weight/expected‑Δ for Viewer role)

Plus `hover`, `focus-visible`, `disabled`, `active/selected`.

**Reference:** `States.html` shows all six × the six Tier 1 components.

---

## 6. Accessibility contract

- All interactive elements keyboard‑reachable. `:focus-visible` ring at 2px `--primary`.
- Color is **never the only signal**: status pills carry text, risk uses shape+color, engine bars have numeric labels.
- Charts: data‑table fallback + ARIA descriptions.
- Respect `prefers-reduced-motion` and `prefers-color-scheme`.
- Minimum target 32×32 (icon buttons), 44×44 on mobile.
- Contrast **AA minimum** on all text, AAA for body.

---

## 7. Implementation notes

### Port directly
- **Design tokens** verbatim.
- **All `styles.css` classes** — copy as source of truth or translate to Tailwind preserving **exact token references** and class structure.
- **Per‑workspace CSS** (`overview.css`, `ops.css`, `policy.css`, `replay.css`, `backtests.css`, `states.css`, `design-system.css`) — keep modular.
- **Icon set** (`icons.jsx`) — Lucide‑compatible names; swap if already using Lucide but keep names.

### Reshape for production
- Components use `Object.assign(window, {...})` for cross‑file sharing (prototype constraint). Convert to proper ES module exports.
- Data is hard‑coded per file; move into a typed API layer (contracts in §8).
- Anchors (`href="Engine Comparison.html"`) become real router transitions. Preserve back‑links.

### DO NOT port
- `tweaks-panel.jsx` — runtime design‑tweak panel, prototype only.
- `useTweaks` hook + `EDITMODE-BEGIN` / `EDITMODE-END` blocks.
- `<script type="text/babel">` loaders — compile JSX ahead of time.

### Recommended drop‑in order
1. Tokens + reset + typography.
2. Shell: `TopBar`, `LeftNav`, `ContextPane`. Wire router.
3. Decision workspace cards (one at a time): Hero → Evidence → Risk → Chart → Scenario → Disagreement.
4. Engine Comparison: Matrix → Alignment → Methodology → Synthesis.
5. Overview (Health, Triage, Activity, Regime).
6. Ops, Policy, Replay, Backtests.
7. All 6 states per component. `prefers-reduced-motion`, `prefers-color-scheme`.
8. Lighthouse: AA contrast (AAA body), zero CLS, 100% keyboard nav.

---

## 8. Data contracts (first pass)

Extracted from the prototype. Refine against real engine outputs.

```ts
type Stance     = 'buy' | 'hold' | 'sell' | 'trim';
type RiskLevel  = 'low' | 'moderate' | 'elevated' | 'high';
type RecStatus  = 'fresh' | 'provisional' | 'published' | 'pending' | 'stale' | 'degraded';
type Severity   = 'info' | 'caution' | 'breach';

interface Recommendation {
  id: string;                        // "REC-2026-0419-NVDA-L"
  ticker: string;
  name: string;
  sector: string;
  universe: string;
  stance: Stance;
  status: RecStatus;
  version: number;
  ageMinutes: number;
  horizon: '1M' | '3M' | '6M' | '1Y';
  proposedWeight: number;            // 0.042 = +4.2%
  expectedDelta: number;             // 0.048
  confidence: { model: number; data: number; operational: number }; // 0..1 each
  thesis: string;
  evidence: Evidence[];
  engines: Engine[];
  dispersion: number;                // 0..1
  risk: RiskConstraint[];
  flags: Array<{ kind: Severity; text: string }>;
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
  key: string;                       // "momentum"
  name: string;
  stance: Stance;
  confidence: number;                // 0..1
  weight: number;                    // 0..1, portfolio weight contributed
  priceTarget?: number;
  weightChangeBps: number;           // +480 bps
  horizon: string;
  risk: RiskLevel;
  drivers: string[];                 // top 3
  ignores: string[];                 // methodology transparency
  note: string;                      // caveat or down-weight reason
  dataFreshnessMin: number;
}

interface PolicyRule {
  id: string;
  category: 'concentration' | 'liquidity' | 'drawdown' | 'var' | 'sector' | 'custom';
  name: string;
  threshold: number;
  severity: Severity;
  scope: 'portfolio' | 'position' | 'sector';
  enabled: boolean;
}

interface BacktestRun {
  id: string;
  name: string;
  strategy: string;
  universe: string;
  start: string; end: string;        // ISO month
  rebalance: 'Daily' | 'Weekly' | 'Monthly' | 'Quarterly' | 'Event';
  costs: string;                     // "12bp"
  status: 'live' | 'saved' | 'archived';
  curve: Array<{ t: number; v: number }>;
  totalReturn: number;
  cagr: number;
  sharpe: number;
  sortino: number;
  maxDD: number;                     // negative
  winRate: number;
  trades: number;
}

interface ReplayEvent {
  id: string;
  t: number;                         // 0..1 position on scrub
  when: string;                      // "Jan 18, 09:42"
  title: string;
  kind: 'data' | 'engine' | 'action' | 'market';
  engineDeltas?: Record<string, { from: number; to: number }>;
}
```

---

## 9. Open questions for PM

1. Engine weights — fixed per strategy, dynamic per regime, or user‑tuned?
2. Who can `Publish`? Role model details (Analyst / PM / Ops / Viewer already referenced).
3. SLA for data freshness before a rec auto‑degrades to `stale`?
4. Replay snapshots: include LLM traces, or numeric only?
5. Mobile — read‑only, or do PMs take actions (beyond paper)?
6. Dark/light — user preference or org policy?
7. Policy rule sim — does it re‑run against live book or a fixed test set?
8. Backtest → Paper promote — auto‑deploy to paper or explicit sign‑off by PM?

---

## 10. Out of scope for this package

Still to design — ping the designer before shipping:

- **Paper portfolio** — live P&L on promoted strategy, slippage reality check, production‑gate
- **Universe browser** — factor exposures, liquidity filters, universe builder
- **Onboarding / sign‑in** — role assignment, team invites, entitlements
- **Settings** — notification prefs, density, theme, API keys

---

## 11. Web stack — React + Vite + TS + Tailwind

```
npm create vite@latest quantpipeline-web -- --template react-ts
cd quantpipeline-web
npm i -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**Tokens → Tailwind.** Import `tokens.css` from `main.tsx`, then reference in `tailwind.config.js`:
```js
theme: {
  extend: {
    colors: {
      ink: 'var(--ink)', 'ink-2': 'var(--ink-2)', 'ink-3': 'var(--ink-3)',
      surface: 'var(--surface)', 'surface-2': 'var(--surface-2)',
      line: 'var(--line)', 'line-strong': 'var(--line-strong)',
      primary: 'var(--primary)',
      pos: 'var(--pos)', caution: 'var(--caution)', breach: 'var(--breach)',
      accent: 'var(--accent)', 'accent-2': 'var(--accent-2)',
    },
    fontFamily: {
      display: ['Fraunces','serif'],
      sans: ['"Inter Tight"','system-ui','sans-serif'],
      mono: ['"JetBrains Mono"','ui-monospace','monospace'],
    },
    borderRadius: { sm: 'var(--r-sm)', md: 'var(--r-md)', lg: 'var(--r-lg)', xl: 'var(--r-xl)' },
  },
},
```

**Routing:** `react-router-dom` v6. One route per IA path. Keep `thesis` / `horizon` / `scenario` in a `DecisionContext` persisting across `/decision/:id/*`.

**State:** Zustand or TanStack Query — not Redux. Per‑workspace stores, not global.

---

## 12. iOS stack — SwiftUI

**Target:** iOS 17+ (iPhone + iPad). `NavigationSplitView` at `regular` size class, stacked otherwise.

| Prototype | SwiftUI |
|---|---|
| `IOSNav` large title | `.navigationTitle(..., displayMode: .large)` |
| Grouped card | `List { Section {} }` `.insetGrouped` |
| `IOSTabBar` | `TabView` + `.tabItem` |
| Blur bottom bar (publish) | `.safeAreaInset(edge: .bottom) { ... .background(.ultraThinMaterial) }` |
| Scope chip strip | Horizontal `ScrollView` of pills |
| Publish sheet (Face ID) | `.sheet` + `LAContext.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics)` |
| Scenario controls | `Form` + `Slider` / `Toggle` + live delta preview in header |
| Replay scrubber | `Slider` bound to `selectedSnapshotIndex` |
| Sparklines / confidence history | Swift Charts (`LineMark`, `AreaMark`) |
| Engine bars | Swift Charts `BarMark` or `GeometryReader` |

**Colors:** add Color Sets (`ink`, `ink2`, `ink3`, `surface`, `surface2`, `surface3`, `separator`, `blue`, `green`, `red`, `orange`, `indigo`) with light+dark variants. Prefer system colors (`Color(.label)`, `.systemBackground`) where the design matches.

**Type:** SF Pro default. Large titles `.system(size: 34, weight: .bold)`; body `17`; captions `13`; mono metrics `.system(.caption, design: .monospaced)`.

**Permissions / state:**
- Face ID on **Promote to paper**. Live publish is **disabled on mobile** — direct user to desktop.
- `@AppStorage` for last‑viewed decision + scope chip selection.
- Auto‑lock after 2 min inactivity (user configurable).

**Navigation:**
- iPhone: 5‑tab `TabView` (Today · Decisions · Compare · Alerts · Me), each with its own `NavigationStack`.
- iPad: `NavigationSplitView` three‑column (sidebar · list · detail) — matches `ios/screen-ipad.jsx`.

---

## 13. Shared contracts (web ↔ iOS)

Both clients consume the same API. The **confidence trio** is non‑negotiable on both platforms — always render all three scores, never collapse into one number.

See §8 for canonical TypeScript types. For Swift, mirror as `Codable` structs with identical field names (snake_case on the wire, camelCase in Swift via `.convertFromSnakeCase`).

---

## 14. Version

- Prototype version: **v1.0** (Jan 2026)
- Workspaces implemented: Overview, Decision, Comparison, Replay, Policy, Ops, Backtests, iOS (12 screens), States reference, Design System
- Next: Paper portfolio → Universe browser → Onboarding / Team
