# FINRLX UX/UI Transformation Master Plan

**Document purpose:** This document is intended to be placed in the FINRLX project under `DOCS/FINRLX_UX_UI_TRANSFORMATION_MASTER_PLAN.md` and used as the operating plan for a full-site UX/UI transformation executed through Claude Code in PyCharm.

**Product context:** FINRLX is a private decision-intelligence platform for medium-term investing. It includes a Next.js/TypeScript frontend, FastAPI backend, research/governance workflows, recommendation lifecycle, paper/shadow research concepts, RL/FinRL-X research constraints, admin/ops surfaces, design assets, and prior handoff documentation.

**Primary problem to solve:** The current site feels overloaded, non-intuitive, text-dense, small-font, and difficult to navigate. The redesign must not be a cosmetic facelift. It must restructure the product experience around decision workflows, source-grounded evidence, portfolio/risk awareness, and governance/trust.

**Required execution style:** Work in phased sprints. Each phase must have explicit gates, automated tests, screenshots, accessibility checks, self-audit, and a handoff report before moving to the next phase. Do not rewrite the entire product in one pass.

---

## 0. Non-negotiable execution rules for Claude Code

Claude must follow these rules throughout the full program:

1. **Inspect before editing.** Always inspect the current repo, route structure, design folder, `design/handoff-package`, existing tokens, current components, existing tests, and existing handoff docs before changing code.
2. **Use the existing design foundation.** FINRLX already has design assets and a handoff package. Do not discard them. Review them and either adopt, extend, or explicitly justify changes.
3. **No unsupported finance claims.** The UI must not imply guaranteed returns, autonomous investing, live trading, broker execution, or risk-free recommendations.
4. **Research-only AI/RL language.** AI, RL, FinRL-X, backtesting, imported research candidates, and paper/shadow concepts must be clearly labeled as research/governance tools unless the existing backend explicitly supports otherwise.
5. **No hidden mock truth.** Mock data may be used for visual scaffolding only if clearly labeled and isolated. Do not present mock data as real FINRLX system state.
6. **Readable typography.** Default UI must be readable at normal laptop sizes. Avoid tiny 11-12px enterprise text except for secondary metadata.
7. **Decision-first UX.** Every major dashboard section must answer: What changed? Why does it matter? What requires action? What evidence supports it? How fresh is the data? What are the limitations?
8. **Mobile is not a squeezed desktop.** Tables must become cards or progressive disclosure on mobile. Dense ops surfaces may be marked desktop-preferred only with clear fallback UX.
9. **No broad rewrites without tests.** Prefer reusable shell/components/tokens. Avoid breaking backend contracts. Add/update tests for every meaningful UI or API integration change.
10. **Every phase ends with evidence.** Each phase must produce a report, test logs, screenshot evidence, changed-file list, known gaps, and next-step recommendation.

---

## 1. Skills strategy: what Claude must install, audit, create, and use

### 1.1 Why skills matter for this redesign

Agent Skills are modular instruction/resource folders that can guide Claude for repeated specialized work. Anthropic describes Skills as pre-built or custom packages that Claude can automatically use when relevant. They are useful here because FINRLX requires repeated enforcement of design quality, finance disclaimers, governance language, accessibility, visual QA, and handoff discipline.

Official reference:
- Anthropic Agent Skills overview: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- Anthropic public skills repository: https://github.com/anthropics/skills
- Anthropic frontend-design skill: https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md
- Anthropic engineering note on skills and security: https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills

### 1.2 Mandatory first step: local skill inventory

Before installing or creating anything, Claude must inspect the local repo for project skills:

```bash
find . -maxdepth 4 -type f -iname "SKILL.md" -print
find . -maxdepth 4 -type d -iname "skills" -print
```

On Windows PowerShell:

```powershell
Get-ChildItem -Recurse -Filter SKILL.md -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
Get-ChildItem -Recurse -Directory -Filter skills -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
```

Claude must record:

- Which skills already exist.
- Which skills were actually used.
- Which skills were missing.
- Which skills were newly created.
- Which external skills were evaluated but not installed.
- Any security concerns.

Required report section:

```text
DOCS/handoff/FINRLX_UX_SKILL_INVENTORY.md
```

### 1.3 Existing FINRLX project skills to use if present

If any of the following project-local skills exist, Claude must read and use them before relevant work:

| Skill | Expected use |
|---|---|
| `fintech-disclaimer-and-marketing-guard` | Prevents unsafe investment promises, broker/trade language, misleading AI/RL claims. |
| `feature-flag-kill-switch` | Ensures risky UI changes are gated or reversible when appropriate. |
| `recommendation-object-provenance` | Ensures recommendation cards expose source/provenance/freshness. |
| `backtest-hygiene-gate` | Ensures backtest/RL UI does not imply future performance or production influence. |
| `replay-determinism-harness` | Supports deterministic verification when touching replay/backtest/decision flows. |

If they are missing, Claude must not pretend they exist. Instead, record the gap and create a minimal project-local substitute only if safe and scoped.

### 1.4 External skills to evaluate and optionally install

Claude should evaluate the following trusted or high-value external skills/resources. Installation must be deliberate and documented.

#### A. Anthropic `frontend-design` skill — recommended

Purpose: improve visual quality, layout polish, spacing, hierarchy, and avoid generic AI-looking UI.

Source:
- https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md

Possible install command if the local skills CLI is available:

```bash
npx skills add https://github.com/anthropics/skills --skill frontend-design
```

If the command is unavailable or inappropriate, Claude must manually inspect the skill instructions and create a repo-local derivative skill only after summarizing what was imported and why.

Use this skill during:

- Design system foundation.
- App shell redesign.
- Home command center redesign.
- Research page redesign.
- Decision pipeline redesign.
- Mobile/tablet pass.

#### B. Vercel `web-design-guidelines` skill — audit before use

Purpose: UI quality, accessibility, usability, performance, and web design checks.

Source:
- https://github.com/vercel-labs/agent-skills/blob/main/skills/web-design-guidelines/SKILL.md
- https://github.com/vercel-labs/agent-skills

Security rule: do not blindly execute remote instructions. Read the skill content first, record what it requires, and only then decide whether to install or copy a safe local subset.

Possible install command if the local skills CLI is available:

```bash
npx skills add https://github.com/vercel-labs/agent-skills --skill web-design-guidelines
```

Use this skill during:

- Accessibility checks.
- Visual QA.
- Responsive QA.
- Final phase gate review.

#### C. shadcn/ui — component foundation, not necessarily a skill

Source:
- https://ui.shadcn.com/
- https://ui.shadcn.com/docs/installation/next

FINRLX already has custom components and Tailwind tokens. Claude must not install shadcn blindly if it conflicts with the existing design system. Instead:

1. Inspect current component library.
2. Compare current approach to shadcn patterns.
3. Reuse FINRLX tokens and components first.
4. Add shadcn-style primitives only if they reduce inconsistency and do not bloat the app.

#### D. Vercel AI Elements / AI SDK UI — evaluate for AI assistant surfaces

Sources:
- https://github.com/vercel/ai-elements
- https://ai-sdk.dev/docs/ai-sdk-ui
- https://elements.ai-sdk.dev/

Use only if the FINRLX AI/research assistant UI requires structured AI message states, source chips, retrieval status, or streaming states. Do not convert FINRLX into a chat-first app.

#### E. Benchmark/UI inspiration resources — do not install

Use these for design research only:

- TradingView: https://www.tradingview.com/
- TradingView features: https://www.tradingview.com/features/
- TradingView screener: https://www.tradingview.com/screener/
- Koyfin: https://www.koyfin.com/
- Finviz: https://finviz.com/
- Finviz map: https://finviz.com/map
- Simply Wall St: https://simplywall.st/
- AlphaSense: https://www.alpha-sense.com/
- TipRanks: https://www.tipranks.com/
- TrendSpider: https://trendspider.com/
- YCharts: https://ycharts.com/
- TIKR: https://www.tikr.com/

### 1.5 Project-local skills Claude should create

Claude should create project-local skills under `.claude/skills/` only after confirming the project convention. If `.claude/skills/` is missing, create it. Every skill must include a `SKILL.md` with clear YAML frontmatter and short, specific instructions.

#### Skill 1: `finrlx-ux-redesign-director`

Purpose: governs the full redesign philosophy.

Activation: any FINRLX UX/UI redesign, app shell, navigation, dashboard, or responsive work.

Core instructions:

- Use decision-first UX.
- Prefer fewer, stronger modules over many dense widgets.
- Enforce readable typography.
- Preserve governance/trust language.
- Use design/handoff assets.
- Avoid generic SaaS admin templates.

#### Skill 2: `finrlx-fintech-dashboard-patterns`

Purpose: governs dashboard/card/table/chart patterns.

Activation: dashboards, radar tables, portfolio/risk surfaces, market data views.

Core instructions:

- Every metric needs context, freshness, and action relevance.
- Tables need loading/empty/error/stale states.
- Mobile tables become cards.
- Market/portfolio data must not imply execution.
- Use semantic risk/status badges.

#### Skill 3: `finrlx-ai-ux-governance`

Purpose: governs AI/RL/research assistant UX.

Activation: AI assistant, research copilot, RL, backtest, imported candidate, model status, chat-like UI.

Core instructions:

- AI is an assistant, not a decision-maker.
- Show sources/provenance.
- Show limitations.
- Never present AI/RL output as guaranteed, live-trading, or broker-executable.
- Avoid blank “ask anything” as the only UX; provide guided prompts.

#### Skill 4: `finrlx-visual-qa-accessibility-gate`

Purpose: quality gate for every visual phase.

Activation: before phase completion.

Core instructions:

- Run typecheck, tests, build.
- Capture screenshots for mobile/tablet/desktop.
- Run accessibility checks where available.
- Check font sizes and contrast.
- Verify no horizontal overflow except explicitly desktop-only admin surfaces.

#### Skill 5: `finrlx-handoff-evidence-packager`

Purpose: produces review-ready evidence.

Activation: every phase completion.

Core instructions:

- Create phase report.
- Save test outputs.
- Save screenshots.
- Save changed-file list.
- Save known limitations.
- Prepare review package without node_modules, build artifacts, DBs, logs, or secrets.

### 1.6 Skill usage protocol for every phase

At the start of every phase, Claude must write in the phase report:

```text
Skills consulted:
- [skill name] — used for [purpose]
- [skill name] — used for [purpose]

Skills not found:
- [skill name] — impact and mitigation

External sources reviewed:
- [source] — what was learned and how it influenced the implementation
```

Before coding, Claude must read relevant skills. After coding, Claude must run the visual/accessibility/handoff gate skill.

---

## 2. External benchmark and research references Claude must use

Claude should use external references for learning and pattern recognition, but must implement a FINRLX-specific product experience rather than copying any competitor.

### 2.1 Financial product benchmarks

| Product | Source | What Claude should study | FINRLX takeaway |
|---|---|---|---|
| TradingView | https://www.tradingview.com/ and https://www.tradingview.com/features/ | Fast chart access, market summary, screeners, alerts | Reduce friction to primary workflow; do not bury chart/research under unrelated widgets. |
| Koyfin | https://www.koyfin.com/ | Professional research dashboards, portfolios, reports | FINRLX should feel like a serious research workspace, not a retail gamified app. |
| Finviz | https://finviz.com/ and https://finviz.com/map | Screener speed, market maps, dense market scan | Use radar/heatmap patterns, but improve readability and evidence depth. |
| Simply Wall St | https://simplywall.st/ | Visual stock reports, portfolio clarity | Use visual summaries and readable insight cards without hiding assumptions. |
| AlphaSense | https://www.alpha-sense.com/ | AI-powered source-heavy research | AI assistant must be source-grounded and evidence-driven. |
| TipRanks | https://www.tipranks.com/ | Multi-signal ratings and stock research | Use factor/provenance breakdown, not a magic score. |
| TrendSpider | https://trendspider.com/ | Technical analysis automation and backtesting workflows | Use automation/backtest UX carefully with limitations. |
| YCharts | https://ycharts.com/ | Advisor-grade research and portfolio visuals | Good model for professional portfolio/risk communication. |
| TIKR | https://www.tikr.com/ | Fundamental research and global screener | Strong reference for company research depth. |

### 2.2 User-pain and forum references

Claude should read and summarize these before major IA/design phases:

- TradingView friction complaint: https://www.reddit.com/r/TradingView/comments/1e9aooo/tradingview_nobody_gives_a_damn_about_90_of_your/
- AI conversational UI design discussion: https://www.reddit.com/r/UXDesign/comments/1ju90qt/what_ive_learned_from_18_mths_of_ai/
- AI chatbot as bad UX band-aid discussion: https://www.reddit.com/r/UXDesign/comments/1mnf2e6/the_ai_chatbot_is_not_a_superhero_its_a_bandaid/
- AI investing workflow discussion: https://www.reddit.com/r/investing/comments/1rvlej9/do_any_of_you_use_ai_to_analyze_your_investment/
- Finviz/value investing pain: https://www.reddit.com/r/ValueInvesting/comments/1s3acqs/is_there_a_finviz_alternative_thats_actually/
- AI-generated UI consistency discussion: https://www.reddit.com/r/webdev/comments/1sa6c49/every_project_i_build_ends_up_with_inconsistent_ui/

Research takeaways Claude must apply:

1. Do not block users from their primary task.
2. Avoid bloated generic dashboards.
3. Do not use AI chat as a band-aid for unclear UX.
4. Provide guided prompts and workflow actions.
5. Provide a real research layer under AI summaries.
6. Build a design playbook before relying on AI-generated UI.

### 2.3 Professional UX sources

Claude should reference these during audit/design-system phases:

- Nielsen Norman Group dashboard/data visualization resources: https://www.nngroup.com/videos/data-visualizations-dashboards/
- Nielsen Norman Group AI product design study guide: https://www.nngroup.com/articles/designing-ai-study-guide/
- Nielsen Norman Group generative UI article: https://www.nngroup.com/articles/generative-ui/
- Smashing Magazine dashboard design/de-cluttering: https://www.smashingmagazine.com/2021/11/dashboard-design-research-decluttering-data-viz/
- UX Pilot dashboard design principles: https://uxpilot.ai/blogs/dashboard-design-principles
- UXDesign.cc critique of generic LLM AI design patterns: https://uxdesign.cc/thinking-past-the-cliche-of-llms-ai-design-patterns-c9b849fce9e8

---

## 3. Target FINRLX product architecture

The redesigned FINRLX should organize the product around six primary areas:

```text
Home / Command Center
Research
Decisions
Portfolio & Risk
Insights
Ops & Governance
```

### 3.1 Home / Command Center

Purpose: show what changed, what matters, and what needs review.

Core modules:

- Market pulse
- Portfolio/watchlist impact
- Decision queue
- Opportunity radar
- Data freshness
- Governance/safety status
- Research assistant preview

### 3.2 Research

Purpose: ticker, company, sector, and theme research.

Core modules:

- Global ticker/company search
- Company overview
- Fundamentals
- Technicals
- News/events
- Peer comparison
- Thesis/evidence drawer
- Source-grounded assistant

### 3.3 Decisions

Purpose: recommendation lifecycle and approval workflow.

Core modules:

- Draft / staged / approved / published / blocked states
- Risk override explanations
- Evidence review
- Audit trail
- Publication gates
- Decision history

### 3.4 Portfolio & Risk

Purpose: exposure, concentration, and scenario risk.

Core modules:

- Allocation
- Factor exposure
- Sector exposure
- Concentration risk
- Drawdown and volatility
- Correlation clusters
- Upcoming earnings exposure
- Scenario stress

### 3.5 Insights

Purpose: decision-linked research events, not generic news.

Core modules:

- Watchlist-moving news
- Earnings changes
- Signal disagreements
- Macro events
- Model/backtest changes
- Research alerts

### 3.6 Ops & Governance

Purpose: system health and governance visibility.

Core modules:

- Ingestion status
- Feature freshness
- Engine health
- RL/shadow status
- Backtest registry
- Model/data lineage
- Publication gates
- Audit events

---

## 4. Design system direction

### 4.1 Visual identity

FINRLX should look like:

- modern institutional fintech
- calm and analytical
- readable and spacious
- serious but not boring
- trustworthy and governed
- not a crypto casino
- not a generic SaaS template
- not a tiny-font admin console

### 4.2 Typography targets

| Element | Target size |
|---|---:|
| Page title | 28–36px |
| Section title | 20–24px |
| Card title | 16–18px |
| Body text | 15–16px |
| Table text | 14–15px |
| Metadata/caption | 12.5–13.5px minimum |
| Buttons | 14–16px |

### 4.3 Layout principles

- Use fewer cards with clearer hierarchy.
- Use page headers with clear primary action.
- Avoid more than 3 major columns on desktop.
- Mobile layouts must stack by priority.
- Tables must offer density modes if needed.
- Use progressive disclosure for complex governance and audit details.

### 4.4 Data-state standards

Every data-heavy component must have:

- loading state
- empty state
- error state
- stale-data state
- last-updated timestamp
- source/provenance where relevant
- action or next step

---

## 5. Phase-by-phase implementation plan with gates

## Phase 0 — Repo UX audit, skill inventory, and benchmark synthesis

**Goal:** understand the current product and create the baseline before redesigning.

**Claude must inspect:**

- `frontend/src/app/**`
- `frontend/src/components/**`
- `frontend/src/services/**`
- `frontend/src/contexts/**`
- `frontend/src/app/globals.css`
- `frontend/tailwind.config.ts`
- `design/**`
- `design/handoff-package/**`
- `DOCS/handoff/**`
- `.claude/skills/**` if present
- backend API route files relevant to overview, decisions, risk, news, engines, features, health

**Deliverables:**

- Current route/page inventory.
- Component inventory.
- Design-token inventory.
- UX pain map.
- Visual-density assessment.
- Typography assessment.
- Navigation critique.
- Existing skill inventory.
- External benchmark synthesis.
- Redesign backlog with prioritized phases.

**No major product code changes allowed in this phase.**

**Required outputs:**

```text
DOCS/handoff/FINRLX_UX_PHASE_0_AUDIT_REPORT.md
DOCS/handoff/FINRLX_UX_PHASE_0_PAGE_INVENTORY.csv
DOCS/handoff/FINRLX_UX_PHASE_0_SKILL_INVENTORY.md
DOCS/handoff/FINRLX_UX_PHASE_0_BENCHMARK_SYNTHESIS.md
DOCS/handoff/FINRLX_UX_PHASE_0_REDLINE_BACKLOG.md
```

**Gate 0:**

Claude may not proceed to Phase 1 unless:

- All major routes are listed.
- The design folder and handoff package were inspected.
- Existing skills were inventoried honestly.
- At least 8 competitor/reference products were summarized.
- At least 5 user-pain sources were summarized.
- The report identifies what to keep, merge, remove, redesign, or defer.

---

## Phase 1 — Skill setup and FINRLX redesign playbook

**Goal:** create a durable design/process instruction layer before code changes.

**Tasks:**

1. Audit current skills.
2. Install or locally mirror trusted skills if appropriate.
3. Create project-local FINRLX redesign skills.
4. Create `DOCS/FINRLX_UX_UI_REDESIGN_PLAYBOOK.md`.
5. Define canonical design vocabulary.
6. Define forbidden language and forbidden UI patterns.

**Required project-local skills:**

```text
.claude/skills/finrlx-ux-redesign-director/SKILL.md
.claude/skills/finrlx-fintech-dashboard-patterns/SKILL.md
.claude/skills/finrlx-ai-ux-governance/SKILL.md
.claude/skills/finrlx-visual-qa-accessibility-gate/SKILL.md
.claude/skills/finrlx-handoff-evidence-packager/SKILL.md
```

**Gate 1:**

- Every created skill has valid `SKILL.md` frontmatter.
- No untrusted remote skill is installed without audit.
- Playbook exists and is referenced from the phase report.
- Claude records how each skill will be used in future phases.
- No product UI is redesigned yet unless needed to support the playbook.

---

## Phase 2 — Information architecture and navigation model

**Goal:** simplify FINRLX from many screens into clear workflows.

**Tasks:**

1. Map current routes to target architecture.
2. Define new top-level navigation.
3. Define page roles and primary actions.
4. Identify redundant or confusing pages.
5. Define route migration plan.
6. Define breadcrumb/command palette/search behavior.
7. Define mobile navigation rules.

**Recommended target navigation:**

```text
Home
Research
Decisions
Portfolio & Risk
Insights
Ops & Governance
Settings
```

**Deliverables:**

```text
DOCS/handoff/FINRLX_UX_PHASE_2_INFORMATION_ARCHITECTURE.md
DOCS/handoff/FINRLX_UX_PHASE_2_ROUTE_MIGRATION_MAP.csv
DOCS/handoff/FINRLX_UX_PHASE_2_NAVIGATION_SPEC.md
```

**Gate 2:**

- Every existing route has a target home: keep, merge, move, rename, or retire.
- Every target product area has a primary user job.
- Mobile navigation is defined.
- No dead-end route is introduced.
- Claude must not delete routes without compatibility or redirect plan.

---

## Phase 3 — Design system foundation

**Goal:** fix the visual foundation before redesigning pages.

**Tasks:**

1. Review existing `globals.css`, Tailwind tokens, design assets, and handoff styles.
2. Define readable typography scale.
3. Define spacing/density modes.
4. Define semantic color tokens for success/caution/risk/info/governance/stale.
5. Standardize cards, badges, buttons, panels, tables, page headers, empty states.
6. Add or update core UI primitives.
7. Create visual examples page or component sandbox if compatible.

**Potential files:**

```text
frontend/src/app/globals.css
frontend/tailwind.config.ts
frontend/src/components/ui/**
frontend/src/components/layout/**
frontend/src/components/finrlx/**
DOCS/FINRLX_UX_UI_REDESIGN_PLAYBOOK.md
```

**Gate 3 testing:**

```bash
cd frontend
npm run typecheck
npm run test:ci
npm run build
```

If Playwright is configured:

```bash
cd frontend
npm run e2e:ci
```

**Gate 3 acceptance:**

- Base text is readable.
- Components have consistent spacing and hierarchy.
- Light/dark mode still works if supported.
- Existing pages are not visually broken.
- No accessibility regression is introduced.
- Screenshot evidence exists for desktop/tablet/mobile.

---

## Phase 4 — App shell and global navigation redesign

**Goal:** make the entire product feel coherent and navigable.

**Tasks:**

1. Redesign app shell.
2. Simplify sidebar/topbar.
3. Add clear page headers.
4. Add product-area grouping.
5. Add persistent governance/data status where useful.
6. Improve command palette/search if present.
7. Add mobile navigation pattern.
8. Preserve authentication and feature-flag behavior.

**Potential files:**

```text
frontend/src/components/shell/AppShell.tsx
frontend/src/components/shell/**
frontend/src/components/navigation/**
frontend/src/app/layout.tsx
frontend/src/contexts/**
```

**Gate 4 acceptance:**

- Users can understand where they are.
- Core workflows are reachable in one or two clicks.
- Navigation does not overwhelm the screen.
- Mobile navigation works without horizontal overflow.
- Authenticated/unauthenticated states still work.
- Existing routes remain accessible or redirected intentionally.

---

## Phase 5 — Home / Command Center redesign

**Goal:** replace the overloaded opening screen with a decision-oriented command center.

**Tasks:**

1. Build `Home / Command Center` page.
2. Show Market Pulse.
3. Show Portfolio/Watchlist Impact.
4. Show Decision Queue.
5. Show Opportunity Radar.
6. Show Data Freshness.
7. Show Governance/Safety Status.
8. Show Research Assistant Preview with guided prompts.
9. Connect to existing APIs where possible.
10. Use clearly labeled fallback states where data is unavailable.

**Potential files:**

```text
frontend/src/app/page.tsx
frontend/src/components/home/**
frontend/src/services/api.ts
frontend/src/components/feedback/**
```

**Gate 5 acceptance:**

- Home answers: what changed, what matters, what needs review.
- No “trade/buy/execute” language exists.
- Every module has loading/empty/error/stale state.
- Data freshness appears.
- Mobile uses cards, not crushed tables.
- Governance status is visible.

---

## Phase 6 — Research workflow redesign

**Goal:** make ticker/company research understandable and evidence-driven.

**Tasks:**

1. Create a research landing/search flow.
2. Redesign ticker/company overview.
3. Add evidence summary cards.
4. Add fundamentals/technicals/news panels.
5. Add peer comparison.
6. Add source-grounded assistant panel.
7. Add thesis/evidence drawer.
8. Add source and freshness metadata.

**Benchmark references:**

- TIKR for fundamentals depth.
- Koyfin for professional research workspace.
- Simply Wall St for visual summary clarity.
- AlphaSense for source-grounded research.

**Gate 6 acceptance:**

- Users can search and understand a ticker/company quickly.
- Research sections are not walls of text.
- Evidence and limitations are visible.
- AI assistant does not replace structured UX.
- Data states are handled.

---

## Phase 7 — Decision Pipeline redesign

**Goal:** make recommendation lifecycle and approval state intuitive.

**Tasks:**

1. Redesign decision pipeline overview.
2. Show draft/staged/approved/published/blocked states.
3. Add recommendation cards with provenance.
4. Add risk override explanations.
5. Add audit trail drawer.
6. Add gate checklist.
7. Add compare/review actions.
8. Preserve backend contract and safety states.

**Gate 7 acceptance:**

- Every recommendation state is visually distinct.
- Blocked states explain why.
- Provenance is visible.
- Risk overrides are not hidden.
- Publication gates are readable.
- No unsafe investment language.

---

## Phase 8 — Portfolio & Risk redesign

**Goal:** make risk and exposure understandable at a glance.

**Tasks:**

1. Redesign portfolio overview.
2. Show allocation/exposure cards.
3. Show factor/sector exposure.
4. Show concentration risk.
5. Show drawdown/volatility.
6. Show correlation clusters if available.
7. Show upcoming earnings exposure if available.
8. Add risk action queue.

**Benchmark references:**

- Koyfin portfolio tools.
- YCharts advisor-grade portfolio communication.
- Simply Wall St portfolio command center.

**Gate 8 acceptance:**

- Portfolio risk can be understood within 10 seconds.
- Risk language is clear and conservative.
- Charts are annotated.
- Empty states explain how to add data.
- Mobile version remains usable.

---

## Phase 9 — Insights and research events redesign

**Goal:** replace generic news with decision-linked research events.

**Tasks:**

1. Redesign news/insights page.
2. Prioritize events that affect watchlist, portfolio, decisions, risk, or models.
3. Add filters by ticker, source, severity, and workflow impact.
4. Add source and freshness chips.
5. Add “why this matters” summaries.
6. Preserve raw-source links where available.

**Gate 9 acceptance:**

- Insights are linked to decisions or research context.
- Generic noise is reduced.
- Users can filter and act.
- AI summaries are source-grounded or clearly labeled as summaries.

---

## Phase 10 — Ops & Governance redesign

**Goal:** keep the power of the ops/admin surface while making it scannable.

**Tasks:**

1. Group ops into pipeline health, data freshness, model/research, publication gates, audit.
2. Use clear status cards and progressive disclosure.
3. Reduce tiny-font density.
4. Preserve desktop-preferred complex admin surfaces where appropriate.
5. Add operational alert queue.
6. Add evidence links to logs/reports where available.

**Gate 10 acceptance:**

- Ops users can identify broken/stale systems quickly.
- Governance concepts are visible.
- Dense tables have filters and progressive disclosure.
- Mobile fallback is explicit and not broken.

---

## Phase 11 — AI assistant and evidence drawer UX

**Goal:** integrate AI as a guided research assistant, not a chat-first replacement for UX.

**Tasks:**

1. Add guided prompts by context.
2. Show source chips.
3. Show retrieval/freshness status.
4. Show limitations and required verification.
5. Add “open evidence” actions.
6. Distinguish global search from AI prompt.
7. Add safe empty states.

**AI assistant must never:**

- tell the user to buy/sell/trade;
- imply direct broker execution;
- hide missing source context;
- present backtests as future guarantees;
- present RL candidate output as production recommendation without explicit governance approval.

**Gate 11 acceptance:**

- AI is useful but constrained.
- Sources are visible.
- Blank-chat UX is avoided.
- AI actions integrate with research/decision workflows.

---

## Phase 12 — Full-system QA, accessibility, visual regression, and performance

**Goal:** harden the redesign before production.

**Required commands:**

Frontend:

```bash
cd frontend
npm run typecheck
npm run test:ci
npm run build
npm run e2e:ci
```

Backend if touched or if frontend contract changed:

```bash
cd backend
python -m pytest -q
```

Forbidden language check:

```bash
rg -n "\b(buy now|sell now|trade now|execute trade|connect broker|guaranteed return|risk-free|beat the market|sure profit)\b" frontend DOCS backend || true
```

Large-file / secret sanity check:

```bash
git status --short
git diff --stat
git diff --name-only
```

**Screenshot matrix:**

- 390px mobile
- 768px tablet
- 1024px small desktop
- 1440px desktop
- dark mode if supported
- light mode if supported

**Gate 12 acceptance:**

- No broken routes.
- No build failures.
- No TypeScript failures.
- No obvious a11y regressions.
- No unsafe finance language.
- Screenshots prove responsive quality.
- Phase reports are complete.

---

## Phase 13 — Railway / production verification

**Goal:** verify that the redesign works outside local development.

**Tasks:**

1. Push to GitHub only after local gates pass.
2. Deploy to Railway using existing project process.
3. Verify production frontend load.
4. Verify backend health endpoints.
5. Verify key flows in production.
6. Compare local vs production screenshots.
7. Record deployment SHA and URLs.

**Gate 13 acceptance:**

- Production homepage loads.
- Core routes load.
- API calls do not fail unexpectedly.
- No production-only layout break.
- Deployment evidence is saved.

Required output:

```text
DOCS/handoff/FINRLX_UX_PRODUCTION_VERIFICATION_REPORT.md
```

---

## 6. Standard phase completion report template

Every phase must produce a report using this structure:

```markdown
# FINRLX UX/UI Transformation — Phase X Report

## A. Summary
What changed and why.

## B. Skills Used
List skills read/applied and where.

## C. External References Used
List product/UX/reddit sources used and implementation takeaways.

## D. Files Changed
Table of changed files and purpose.

## E. UX Decisions
Key design decisions and rationale.

## F. Data/API Contract Notes
What endpoints/types were used or changed.

## G. Safety/Governance Notes
How finance/AI/RL safety was preserved.

## H. Testing Evidence
Commands run, pass/fail, logs.

## I. Screenshot Evidence
Paths to screenshots.

## J. Known Limitations
Honest gaps and tradeoffs.

## K. Next Recommended Phase
Exact recommendation.
```

---

## 7. Review package command

After each phase, Claude should prepare a review package or instruct the operator to run this from the project root in PowerShell:

```powershell
$ErrorActionPreference = "Stop"

$root = Get-Location
$stage = Join-Path $root "_review_package_ux_phase"
$zip = Join-Path $root "FINRLX_ux_phase_review_package.zip"

if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
if (Test-Path $zip) { Remove-Item $zip -Force }

New-Item -ItemType Directory -Path $stage | Out-Null

$dirs = @(
    "frontend",
    "backend",
    "DOCS",
    "docs",
    "design",
    ".claude",
    "tests",
    "scripts",
    "infra"
)

foreach ($d in $dirs) {
    if (Test-Path $d) {
        robocopy $d (Join-Path $stage $d) /E `
            /XD node_modules .next dist build coverage .git .venv venv __pycache__ .pytest_cache .mypy_cache .idea .vscode tmp temp backups research `
            /XF *.log *.zip *.tar *.gz *.rar *.7z *.pyc *.sqlite *.sqlite3 *.db *.parquet *.pkl *.joblib `
            | Out-Null
    }
}

$files = @(
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "next.config.js",
    "next.config.mjs",
    "tailwind.config.js",
    "tailwind.config.ts",
    "tsconfig.json",
    "README.md",
    "pyproject.toml",
    "pytest.ini",
    "alembic.ini",
    "docker-compose.yml",
    "Dockerfile",
    ".env.example"
)

foreach ($f in $files) {
    if (Test-Path $f) {
        Copy-Item $f (Join-Path $stage $f) -Force
    }
}

$meta = Join-Path $stage "_review_metadata"
New-Item -ItemType Directory -Path $meta | Out-Null

git status --short | Out-File (Join-Path $meta "git_status_short.txt") -Encoding utf8
git diff --name-only | Out-File (Join-Path $meta "git_diff_name_only.txt") -Encoding utf8
git diff --stat | Out-File (Join-Path $meta "git_diff_stat.txt") -Encoding utf8
git rev-parse --short HEAD | Out-File (Join-Path $meta "git_head_short.txt") -Encoding utf8

Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zip -Force

Write-Host ""
Write-Host "Created review package:"
Write-Host $zip
```

---

## 8. Claude Code launch prompt

Paste this into Claude Code after placing this file in `DOCS/`:

```text
You are working in the FINRLX repository. Read and execute the plan in DOCS/FINRLX_UX_UI_TRANSFORMATION_MASTER_PLAN.md.

Start with Phase 0 only unless the plan explicitly allows otherwise. Do not redesign the product yet. Your task is to perform a deep UX/product/design audit, skills inventory, external benchmark synthesis, and phase-by-phase redesign backlog.

Mandatory requirements:
1. Inspect the current repo before editing anything.
2. Inspect frontend/src/app, frontend/src/components, frontend/src/services, frontend/src/contexts, frontend/src/app/globals.css, frontend/tailwind.config.ts, design/, design/handoff-package/, DOCS/handoff/, and any .claude/skills directory if present.
3. Search for and inventory all SKILL.md files.
4. Review the external benchmark links and user-pain/forum links listed in the master plan.
5. Produce the Phase 0 deliverables exactly as listed in the plan.
6. Do not make broad product UI changes in Phase 0.
7. Be honest about missing files, missing skills, stale docs, and unknowns.
8. If tests or commands cannot run, record the exact reason and do not claim they passed.
9. End with a clear recommendation for Phase 1 and a review package command.

At the end, provide a completion report with changed files, evidence, and any commands run.
```

---

## 9. Initial assumptions

This plan assumes:

1. The project remains Next.js/TypeScript frontend and FastAPI backend.
2. FINRLX remains research/decision-support software, not a broker or trade-execution product.
3. Claude has internet access for benchmark research.
4. Claude is allowed to create local `.claude/skills/` files if missing.
5. Claude should not install arbitrary third-party packages without explaining why and updating tests.
6. The operator will upload phase reports and review packages for external review after each phase.

---

## 10. Success definition

This transformation is successful when FINRLX becomes:

- easier to understand within the first 30 seconds;
- readable without zooming;
- organized around clear workflows;
- visually consistent across pages;
- safe and honest about AI/RL/backtest/recommendation limitations;
- backed by reusable design components and tokens;
- tested across desktop/tablet/mobile;
- documented with evidence after every phase;
- ready for production verification rather than only local demos.
