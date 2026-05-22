# FINRLX UX/UI Transformation — Phase 0 Redline Backlog

> Required by `DOCS/FINRLX_UX_UI_TRANSFORMATION_MASTER_PLAN.md` §5 Phase 0
> "Redesign backlog with prioritized phases."
>
> Every row is grounded in evidence from the current repo (`frontend/src/app/**`,
> `frontend/src/components/**`, `frontend/src/app/globals.css`,
> `frontend/tailwind.config.ts`, `design/handoff-package/**`, the existing
> `DOCS/handoff/**` reports, and the backend API router).
>
> **Phase 0 makes no product UI changes.** This file is the queue that
> Phases 1–13 work through. Each row carries: the gap, the evidence, the
> disposition (keep / merge / move / rename / retire / redesign / defer),
> the phase that owns it, and the gate it must satisfy before it lands.

## 1. Foundation gaps (Phases 1 & 3)

| ID | Gap | Evidence | Disposition | Owning phase | Gate |
|---|---|---|---|---|---|
| F-1 | The five FINRLX redesign skills (`finrlx-ux-redesign-director`, `finrlx-fintech-dashboard-patterns`, `finrlx-ai-ux-governance`, `finrlx-visual-qa-accessibility-gate`, `finrlx-handoff-evidence-packager`) do not exist. | `.claude/skills/` lists only the six pre-existing safety skills. | Create | Phase 1 | Gate 1 |
| F-2 | No design playbook document. | No `DOCS/FINRLX_UX_UI_REDESIGN_PLAYBOOK.md` in repo. | Create | Phase 1 | Gate 1 |
| F-3 | Body text is 13.5 px in default density (`--dens-text: 13.5px`, `frontend/src/app/globals.css:60`). Metadata is 11 px in many components (`Sidebar.tsx:143`, `RecommendationCard`, `decision/page.tsx:71`). | `frontend/src/app/globals.css`, `frontend/src/components/shell/Sidebar.tsx`, `frontend/src/app/decision/page.tsx`. | Redesign typography scale — body 15 px, table 14 px, metadata 12.5 px minimum. Update `globals.css` and `tailwind.config.ts`. | Phase 3 | Gate 3 |
| F-4 | Two density CSS variables exist (`compact` / `default` / `comfortable`) but no consistent UI control surfaces them — there is a topbar density cycle but no per-table density mode. | `TopBar.tsx:11–13, 65–75`. | Keep variables; add per-table density opt-in in Phase 3 design system. | Phase 3 | Gate 3 |
| F-5 | OKLCH tokens already exist; need semantic aliases for `stale`, `shadow-only`, `blocked`, `governance`. | `globals.css:8–106`. Today only `pos / caution / breach / primary / accent` exist. | Add semantic tokens (extend existing palette, do not replace). | Phase 3 | Gate 3 |
| F-6 | No accessibility check in CI. UX-3.1 axe baseline once passed but is not enforced per PR. | `DOCS/handoff/` filenames reference UX-3.1 but no recurring axe job. | Wire axe into `finrlx-visual-qa-accessibility-gate`. | Phase 3 / Phase 12 | Gate 3, Gate 12 |

## 2. Navigation & Information Architecture (Phase 2)

| ID | Gap | Evidence | Disposition | Owning phase | Gate |
|---|---|---|---|---|---|
| N-1 | Two sidebar sections, 11 + 5 entries — flat and ungrouped by product area. | `frontend/src/components/shell/Sidebar.tsx:13–54`. | Restructure into six product areas: Home / Research / Decisions / Portfolio & Risk / Insights / Ops & Governance + Settings. | Phase 2 | Gate 2 |
| N-2 | `/decision`, `/comparison`, `/replay` are siblings in the sidebar; semantically /comparison and /replay are decision sub-views. | `Sidebar.tsx:21–33`. | Move `/comparison` and `/replay` under Decisions (sub-routes or in-page tabs); preserve standalone routes for deep-link compatibility (handled by plan-required compatibility/redirect plan). | Phase 2 + Phase 7 | Gate 2, Gate 7 |
| N-3 | `/profile` and `/templates` are top-level Workspace entries — they belong to Settings or to a Decisions sub-area. | `Sidebar.tsx:24–25`. | Move `/profile` to Settings/Account; keep `/templates` as a Decisions sub-route. | Phase 2 | Gate 2 |
| N-4 | `/admin` (Research lab) is in Operations and is desktop-only — yet still shown to mobile users until they hit the gate page. | `frontend/src/app/admin/page.tsx:29–51`. | Keep desktop-only gate; relocate label and icon under Ops & Governance; hide entry on mobile by default with a "view on desktop" hint. | Phase 2 + Phase 10 | Gate 2, Gate 10 |
| N-5 | `/operator` console exists at top level but is not in the sidebar — operators only get there from deep links inside Decision/Replay/News. | `Sidebar.tsx`, `frontend/src/app/operator/page.tsx`. | Surface under Ops & Governance behind `operator_console` flag. | Phase 2 | Gate 2 |
| N-6 | `/help` is reached only via a TopBar icon; no breadcrumb when deep inside help. | `frontend/src/components/shell/TopBar.tsx:148–157`. | Treat Help as a peer surface accessible from both Settings and TopBar; add contextual help links per workspace (already partially done via `HelpLink`). | Phase 2 + Phase 4 | Gate 2, Gate 4 |
| N-7 | `TopBar` search is a placeholder chip with no behavior. | `TopBar.tsx:122–127`. | Ship a real command palette in Phase 4 — jump-to-route, jump-to-ticker, jump-to-recommendation. | Phase 4 | Gate 4 |
| N-8 | Mobile drawer exists, but the IA underneath needs reshaping so the bottom of the drawer is not just an icon-less laundry list. | `Sidebar.tsx:152–215`, `AppShell.tsx:75–82`. | Re-order entries by product area; respect new IA. | Phase 2 + Phase 4 | Gate 4 |

## 3. Home / Command Center (Phase 5)

| ID | Gap | Evidence | Disposition | Owning phase | Gate |
|---|---|---|---|---|---|
| H-1 | Home already has 9 panels — Decision Queue, Portfolio Impact, Opportunity Radar, Research Events, Research Assistant Preview, Governance Status, Sector Heatmap, Shadow Research Snapshot, System Health. Risk of overload. | `frontend/src/components/home/DecisionCommandCenter.tsx:147–187`. | Re-tier: keep 4 top-tier panels above the fold (queue, radar, governance, portfolio); demote rest to below-the-fold or a "more" drawer. | Phase 5 | Gate 5 |
| H-2 | Greeting copy ("Hi, {name}") is fine but the supporting sentence is dense. Mobile order is correct but the visual hierarchy collapses on small screens. | `DecisionCommandCenter.tsx:96–119`. | Redesign header with prominent "what changed today" sentence + last-updated chip; keep greeting as secondary. | Phase 5 | Gate 5 |
| H-3 | `DataFreshnessBadge` already exists — extend to every Home panel (some panels currently lack a freshness chip). | `frontend/src/components/home/DataFreshnessBadge.tsx`, `DecisionCommandCenter.tsx:109–118`. | Make freshness a required prop on each Home panel. | Phase 5 | Gate 5 |
| H-4 | `ResearchAssistantPreview` is wired with placeholder content. | `frontend/src/components/home/ResearchAssistantPreview.tsx`. | Wire to `/assistant` endpoint in Phase 5; full assistant UX in Phase 11. | Phase 5 + Phase 11 | Gate 5, Gate 11 |

## 4. Research workflow (Phase 6 — currently missing)

| ID | Gap | Evidence | Disposition | Owning phase | Gate |
|---|---|---|---|---|---|
| R-1 | No `/research` top-level route. Ticker/company research has nowhere to live. | `frontend/src/app/` — no research folder. | Add Research hub with company overview, fundamentals, peer comparison, evidence drawer, source-grounded assistant. | Phase 6 | Gate 6 |
| R-2 | `/universe` covers index/sector coverage but does not host per-ticker research. | `frontend/src/app/universe/page.tsx`. | Keep `/universe` as a coverage view; route ticker drill-downs through new `/research`. | Phase 6 | Gate 6 |
| R-3 | `pricechart` and `engines` backends exist and can power a research page. | `backend/app/api/v1/pricechart.py`, `backend/app/api/v1/engines.py`. | Reuse — do not duplicate. | Phase 6 | Gate 6 |

## 5. Decision pipeline (Phase 7)

| ID | Gap | Evidence | Disposition | Owning phase | Gate |
|---|---|---|---|---|---|
| D-1 | `/decision` shows the "current" recommendation only — there is no `/decision/:id`, no list view, no history surface. | `frontend/src/app/decision/page.tsx:32`. | Add an id-based route for deep linking; keep `/decision` as a redirect to the current one. | Phase 7 | Gate 7 |
| D-2 | Decision page mixes Hero / Evidence / Disagreement / Warnings / Chart / Weights / Positions / Risk gauges into one long scroll. | `decision/page.tsx:67–239`. | Move secondary sections (risk gauges, weights, positions) into the right-side `ContextPane`; keep hero + evidence + disagreement + chart on the main column. | Phase 7 | Gate 7 |
| D-3 | Hardcoded risk-gauge values mixed with backend-fed stage data — looks "real" but is stub. | `decision/page.tsx:221–238`. | Replace with `stages.risk_overlay` real metrics or remove until backend-fed (Phase 7). | Phase 7 | Gate 7 |
| D-4 | The action strip ships two HelpLinks plus five secondary actions (Bookmark / Share / Compare / Replay / More) without handlers on desktop. | `decision/page.tsx:90–127`. | Trim — either wire the handlers or hide the buttons. Don't ship dead affordances. | Phase 7 | Gate 7 |
| D-5 | `StatusBadge`, `ConfidenceBlock`, `WeightsTable`, `WarningsBlock` already exist and align with plan principles — keep as primitives. | `frontend/src/components/recommendation/**`. | Reuse — base the redesign on them, do not replace. | Phase 7 | Gate 7 |

## 6. Portfolio & Risk (Phase 8)

| ID | Gap | Evidence | Disposition | Owning phase | Gate |
|---|---|---|---|---|---|
| P-1 | `/risk` and `/paper` are siblings with no shared shell. | `frontend/src/app/risk/page.tsx`, `frontend/src/app/paper/page.tsx`. | Merge under a Portfolio & Risk product area with two sub-views (Paper / Risk) that share an in-page tab strip or sub-nav. | Phase 8 | Gate 8 |
| P-2 | No correlation cluster, scenario stress, or upcoming-earnings exposure surfaces yet. | Backend exposes risk + scenario; no UI consumers. | Add modules in Phase 8 using existing `/risk`, `/scenario`, `/paper` endpoints. | Phase 8 | Gate 8 |
| P-3 | Risk-page KPI strip uses 11px metadata. | `frontend/src/app/risk/page.tsx:73–75`. | Apply Phase-3 typography rules. | Phase 3 + Phase 8 | Gate 3, Gate 8 |

## 7. Insights / News (Phase 9)

| ID | Gap | Evidence | Disposition | Owning phase | Gate |
|---|---|---|---|---|---|
| I-1 | `/news` is a raw RSS feed; no decision/portfolio linking. | `frontend/src/app/news/page.tsx`. | Redesign Phase 9: filter by watchlist / portfolio / decision; add "why this matters" summaries; preserve raw-source link. | Phase 9 | Gate 9 |
| I-2 | Sentiment classification is shown as colored chips with `+0.42`-style scores — readable but not annotated. | `news/page.tsx:13–21`. | Annotate sentiment: "compound score 0.42 (Vader) over N items"; show source freshness per item. | Phase 9 | Gate 9 |

## 8. Ops & Governance (Phase 10)

| ID | Gap | Evidence | Disposition | Owning phase | Gate |
|---|---|---|---|---|---|
| O-1 | `/ops`, `/policies`, `/integrations`, `/admin`, `/operator` are five separate routes, each with their own layout. | `frontend/src/app/ops/page.tsx`, `policies/page.tsx`, `integrations/page.tsx`, `admin/page.tsx`, `operator/page.tsx`. | Group under Ops & Governance product area with a shared landing page and inline sub-routes. Preserve `/admin` desktop-only gate. | Phase 10 | Gate 10 |
| O-2 | Ops page already follows the right shape (KPI strip + queue + health grid + breaches + audit) but uses tiny type and stacks density. | `ops/page.tsx:71–80`, `frontend/src/components/ops/**`. | Apply Phase 3 typography; add progressive disclosure for queue items. | Phase 3 + Phase 10 | Gate 3, Gate 10 |
| O-3 | Policy and Integrations pages render flat cards — no severity badging in the listing. | `frontend/src/app/policies/page.tsx`, `integrations/page.tsx`. | Add semantic status pills, severity sort, and drawer details. | Phase 10 | Gate 10 |

## 9. AI assistant & evidence drawer (Phase 11)

| ID | Gap | Evidence | Disposition | Owning phase | Gate |
|---|---|---|---|---|---|
| A-1 | `ResearchAssistantPreview` is a static panel; `/assistant` API exists but no full assistant UI. | `frontend/src/components/home/ResearchAssistantPreview.tsx`, `backend/app/api/v1/assistant.py`. | Phase 11: ship guided prompts, source chips, retrieval status, "open evidence" actions. Forbidden: blank chat. | Phase 11 | Gate 11 |
| A-2 | Operator console (`/operator`) is a separate, manual paste-in-LLM-context workflow. Useful for governance, distinct from the in-app assistant. | `frontend/src/app/operator/page.tsx`. | Keep as a separate Operator workflow; do not merge with the in-app assistant. Document the boundary in `finrlx-ai-ux-governance` skill. | Phase 11 | Gate 11 |

## 10. QA / Verification (Phases 12 & 13)

| ID | Gap | Evidence | Disposition | Owning phase | Gate |
|---|---|---|---|---|---|
| Q-1 | No recurring screenshot evidence per breakpoint (390 / 768 / 1024 / 1440). | No `DOCS/handoff/screenshots/` for redesign phases. | Establish screenshot matrix in `finrlx-visual-qa-accessibility-gate`. | Phases 3+ | Gates 3–12 |
| Q-2 | `npm run e2e:ci` exists but coverage of redesigned pages will lag. | `frontend/package.json` (read in Phase 1 confirms). | Update Playwright suites as each phase ships. | Phases 3+ | Gates 3–12 |
| Q-3 | Forbidden-language sweep (`rg`) is documented in plan §5 Phase 12 — not yet hooked into pre-commit. | `fintech-disclaimer-and-marketing-guard` skill encodes the rules. | Add a lightweight pre-push hook in Phase 1 if cheap; otherwise enforce at Phase 12 gate. | Phase 1 or Phase 12 | Gate 1 or Gate 12 |
| Q-4 | Railway deployment is referenced (production base URL hardcoded as fallback in `services/api.ts:13–15`). | `frontend/src/services/api.ts:13–15`, `FeatureFlagsContext.tsx:22–23`. | Phase 13 verification: compare local vs production screenshots; record deployment SHA. | Phase 13 | Gate 13 |

## 11. Quick wins (safe to bundle into Phase 3)

These do not block the redesign but are cheap fixes that improve the
visible baseline in Phase 3:

| ID | Quick win | Where |
|---|---|---|
| QW-1 | Replace 11 px metadata with `--ink-3` at 12.5 px on Decision/Risk/Ops pages. | Multiple. |
| QW-2 | Normalize all SKILL.md frontmatter to `type: project` (two existing skills still use `source: project`). | `.claude/skills/feature-flag-kill-switch/SKILL.md`, `.claude/skills/recommendation-object-provenance/SKILL.md`. |
| QW-3 | Delete `tweaks-panel.jsx` reference from any future port — handoff `HANDOFF.md` already labels it "PROTOTYPE ONLY. Do not port." | `design/handoff-package/handoff-package/tweaks-panel.jsx`. |
| QW-4 | Consolidate the duplicated handoff folders (`design/handoff-package/` and `design/handoff-package/handoff-package/`) into a single source-of-truth. | Two-level nesting is confusing; either flatten or document. |

## 12. Defer / out-of-scope for the 13-phase redesign

| ID | Item | Reason |
|---|---|---|
| X-1 | Real broker integration / live order routing. | Plan §0 rule 3 — FINRLX is decision-support, not a broker. |
| X-2 | Marketing site / landing page. | Out of scope of the redesign program. |
| X-3 | New chart library (replace Recharts/D3). | Existing chart components are sufficient for Phases 3–12. |
| X-4 | Multi-tenant white-label theming. | Single-tenant only — defer indefinitely. |

---

## Disposition summary

- **Keep** as-is: 14 routes (legal pages, auth, help, profile, templates,
  feedback, onboarding, paper, risk, comparison, replay, backtests,
  integrations, policies — content stays; typography and layout improve in
  Phase 3).
- **Redesign** in a specific phase: Home (5), Decision (7), Universe → Research (6), News → Insights (9), Ops/Admin/Operator/Policies/Integrations (10), Assistant (11).
- **Move** in the IA: `/profile`, `/comparison`, `/replay`, `/admin`, `/operator`, `/templates`.
- **Create** new: `/research/*` hub, real command palette, semantic
  `stale/shadow-only/blocked/governance` tokens, five Phase-1 skills,
  redesign playbook doc.
- **Retire / not in this program**: broker execution, marketing site, chart
  library swap, multi-tenant theming.
