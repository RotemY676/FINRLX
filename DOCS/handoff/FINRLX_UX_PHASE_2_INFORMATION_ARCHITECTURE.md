# FINRLX UX/UI Transformation — Phase 2 Information Architecture

> Required by `DOCS/FINRLX_UX_UI_TRANSFORMATION_MASTER_PLAN.md` §5 Phase 2.
> Phase 2 is documentation only. Nav code rewrite is Phase 4.

## Skills consulted

- `finrlx-ux-redesign-director` — rule 9 (six product areas), rule 1 (decision-first), rule 8 (one palette).
- `finrlx-fintech-dashboard-patterns` — informs the per-area workspace shape.
- `feature-flag-kill-switch` — every gated route must carry the flag, no exceptions.
- `fintech-disclaimer-and-marketing-guard` — language rules for area names.
- `vercel-web-design-guidelines-mirror` — `aria-current="page"`, semantic nav.
- `recommendation-object-provenance` — protects `/decision/:id` route shape.

## 1. The six product areas + Settings

Top-level navigation has exactly seven entries. No more. Sub-routes live
under their parent area and are reachable via in-page tabs, drawers, or
sub-nav — not through extra sidebar rows.

### 1.1 Home / Command Center

- **Path:** `/`
- **Primary user job:** "Tell me what changed, what needs review, what evidence supports it, and what's stale or blocked — in 5 seconds."
- **Who:** all signed-in users.
- **Lives below:** decision queue, opportunity radar, portfolio impact, research events, governance status, sector heatmap, shadow research, system health, research-assistant preview.
- **Phase that ships its redesign:** 5.

### 1.2 Research

- **Path:** `/research`, `/research/[ticker]`, `/universe`.
- **Primary user job:** "Investigate a ticker, sector, or theme with source-grounded evidence."
- **Who:** analysts, signed-in users.
- **Lives below:** company overview, fundamentals, technicals, news, peer comparison, source-grounded assistant, thesis drawer, universe coverage/readiness.
- **Phase that ships its redesign:** 6.

### 1.3 Decisions

- **Paths:** `/decision` (current), `/decision/[id]`, `/decision/[id]/compare`, `/decision/[id]/replay`, `/templates`.
- **Primary user job:** "Read the current recommendation, challenge it (compare engines, see disagreement), defer or promote it, or replay a historical decision."
- **Who:** analysts, operators.
- **Lives below:** hero, confidence trio, evidence narrative, engine disagreement, weights, positions, warnings, scenario, chart, history, audit trail.
- **Phase that ships its redesign:** 7.

### 1.4 Portfolio & Risk

- **Paths:** `/portfolio` (new tabbed landing), `/portfolio/paper`, `/portfolio/risk`.
- **Primary user job:** "Understand exposure, concentration, drawdown, and scenario risk on the paper portfolio in under 10 seconds."
- **Who:** analysts.
- **Lives below:** allocation, factor / sector exposure, concentration, drawdown / vol, correlation clusters, upcoming earnings exposure, scenario stress.
- **Phase that ships its redesign:** 8.

### 1.5 Insights

- **Path:** `/insights` (replaces `/news`).
- **Primary user job:** "See decision-linked research events filtered by watchlist, portfolio, decision, risk, or model."
- **Who:** all signed-in users.
- **Lives below:** filtered event feed, "why this matters" summaries, source / freshness chips, raw-source link.
- **Phase that ships its redesign:** 9.

### 1.6 Ops & Governance

- **Paths:** `/ops` (landing), `/ops/policies`, `/ops/integrations`, `/ops/operator`, `/ops/lab` (admin / research lab, desktop-only).
- **Primary user job:** "Check pipeline health, data freshness, policy breaches, publication gates, integrations, and audit trail."
- **Who:** operators only.
- **Lives below:** KPI strip, queue, feeds health, engine health, breaches, audit log, policy editor, integrations health, operator console, RL lab (desktop-only).
- **Phase that ships its redesign:** 10.

### 1.7 Settings

- **Paths:** `/settings/profile`, `/settings/help`, `/settings/account` (future).
- **Primary user job:** "Manage my investor profile, find help, sign out."
- **Who:** all signed-in users.
- **Lives below:** investor profile (view / edit, wizard), help center, beta feedback, account settings.
- **Phase that ships its redesign:** part of Phase 4 (placement) + Phase 6/7 (profile-aware pipeline integration); content stays as-is.

## 2. What lives where: route-to-area assignment

Every existing route has a target area. See `FINRLX_UX_PHASE_2_ROUTE_MIGRATION_MAP.csv` for the full table.

## 3. Layout patterns per area

| Area | Layout pattern | Mobile pattern |
|---|---|---|
| Home | 3-column dashboard with tier-1 panels above the fold | Vertical stack ordered queue → radar → portfolio → assistant → governance → events → sector → shadow → health |
| Research | Search-first landing → 2-column ticker workspace (overview left, evidence/assistant right) | Tabbed (overview / fundamentals / technicals / news / peers / assistant) |
| Decisions | Hero strip + main column (evidence / disagreement / chart) + right ContextPane (weights / risk / warnings) | Vertical stack; secondary sections collapse into accordions |
| Portfolio & Risk | 2-column with tabbed sub-nav (Paper / Risk / Scenario) | Tabbed sub-nav stacks vertically |
| Insights | Filter bar + event list + right detail panel | Filter chip strip + event card list; detail opens as full screen |
| Ops & Governance | Tabbed landing (Health / Queue / Policies / Integrations / Audit) | Health KPI strip + collapsible sections; lab gated with "open on desktop" notice |
| Settings | Single-column with sub-nav (Profile / Help / Account) | Single column |

## 4. Navigation principles

1. **Seven top-level entries, no more.** The current 16-entry flat list collapses into seven product-area entries.
2. **Sub-routes live in-page.** `/decision/[id]/compare` and `/decision/[id]/replay` open inside the Decisions workspace, not as sibling sidebar items.
3. **`aria-current="page"`** on the active nav entry (per `vercel-web-design-guidelines-mirror`).
4. **Active state tracks the current URL.** Active highlight matches the area, not the exact path — so `/decision/abc` lights up "Decisions".
5. **Mobile is a drawer.** Same seven entries, full-width labels, no icon-only collapsed state on mobile.
6. **Command palette is the second nav.** Global ⌘K opens an action-search palette that jumps to routes, tickers, recommendations, and operator analyses. Spec lives in `FINRLX_UX_PHASE_2_NAVIGATION_SPEC.md`.
7. **Breadcrumbs** appear in the TopBar for every page two or more levels deep. Format: `Area · Sub-area · Current` (max three crumbs).
8. **No dead-end routes.** Every legacy route is either kept, redirected, moved, or retired with a `next/redirect`. No 404 paths.

## 5. Backward-compatibility / redirect plan

Every retired or moved route gets a `next/redirect` (Next.js 14 App Router supports this via `next.config.js` `redirects()`). Specifically:

| Old path | New path | Mechanism |
|---|---|---|
| `/comparison` | `/decision/[current-id]/compare` (fallback `/decision`) | 308 redirect via `next.config.js` |
| `/replay` | `/decision/[id]/replay` (or kept as legacy list view at `/decisions/replay`) | 308 redirect with query preservation |
| `/news` | `/insights` | 308 redirect |
| `/risk` | `/portfolio/risk` | 308 redirect |
| `/paper` | `/portfolio/paper` | 308 redirect |
| `/policies` | `/ops/policies` | 308 redirect |
| `/integrations` | `/ops/integrations` | 308 redirect |
| `/admin` | `/ops/lab` | 308 redirect (keep desktop-only gate) |
| `/operator` | `/ops/operator` | 308 redirect |
| `/profile` | `/settings/profile` | 308 redirect |
| `/feedback` | `/settings/feedback` (or kept at root for beta clarity) | TBD in Phase 4 |
| `/help` | `/settings/help` (TopBar shortcut preserved) | TopBar link stays, route may be aliased |

Auth, legal, and onboarding routes do **not** move:
- `/login`, `/login/google-finish`, `/signup` stay.
- `/disclaimer`, `/terms`, `/privacy` stay.
- `/onboarding` stays (deep-linked from auth flows).

## 6. Feature-flag treatment

Every gated entry stays gated. `feature-flag-kill-switch` rule: navigation entries hide while flags load, show when their flag is true.

| Area | Flags |
|---|---|
| Home | none |
| Research | `universe_ui` (for universe sub-route) |
| Decisions | none for main; `replay`, `backtests` for sub-routes (backtests may live under Research instead — locked in Phase 6) |
| Portfolio & Risk | `paper_trading`, `risk_ui` |
| Insights | `news_ui` |
| Ops & Governance | `ops_ui`, `policy_ui`, `integrations_ui`, `research_lane` (lab), `operator_console` (operator sub-route) |
| Settings | none |

If all sub-routes of an area are flag-off, the area entry hides entirely.

## 7. Open IA questions resolved in Phase 2

| Question (from playbook §10) | Resolution |
|---|---|
| Should `/decision` and `/decision/:id` be merged? | Keep distinct. `/decision` is a server-side redirect to the latest published `/decision/[id]`. |
| Is `/comparison` a route or in-page tab? | In-page tab at `/decision/[id]/compare`. Legacy `/comparison` becomes a 308 redirect. |
| Is `/operator` user-visible or operator-only? | Operator-only behind `operator_console` flag, surfaced as a sub-route under Ops & Governance. |
| Command palette in Phase 4? | Yes — see `FINRLX_UX_PHASE_2_NAVIGATION_SPEC.md`. |
| "Shadow research" canonical name? | **"Research-only"** for user-facing copy; "shadow lane" stays in internal docs / backend. Locked. |

## 8. Gate 2 compliance (plan §5 Phase 2)

| Gate 2 requirement | Status |
|---|---|
| Every existing route has a target home (keep / merge / move / rename / retire) | Met — `FINRLX_UX_PHASE_2_ROUTE_MIGRATION_MAP.csv` lists all 25. |
| Every target product area has a primary user job | Met — §1.1–§1.7. |
| Mobile navigation is defined | Met — §3 and `FINRLX_UX_PHASE_2_NAVIGATION_SPEC.md`. |
| No dead-end route is introduced | Met — §5 redirect plan covers every move/rename. |
| No routes deleted without compatibility / redirect | Met — §5; no Phase 2 deletions. |

**Gate 2 clears. Proceeding to Phase 3.**
