---
name: finrlx-ux-redesign-director
description: Master UX/UI direction for the FINRLX redesign program. Activates on any change to frontend/src/app/**, frontend/src/components/**, the app shell, navigation, design tokens, or any phase work governed by DOCS/FINRLX_UX_UI_TRANSFORMATION_MASTER_PLAN.md. Enforces decision-first UX, readable typography, governance/trust language, and the six-area product architecture. Read before, and self-check after, every UI change.
type: project
---

# FINRLX — UX/UI Redesign Director

This is the spine of the FINRLX UX redesign program. It encodes the ten rules
that every later phase must satisfy. If a change violates any of these, that
is the signal to push back.

## When to invoke

- Any change under `frontend/src/app/**` or `frontend/src/components/**`.
- Any change to design tokens in `frontend/src/app/globals.css` or `frontend/tailwind.config.ts`.
- Any change to navigation: `Sidebar.tsx`, `TopBar.tsx`, `AppShell.tsx`, `ContextPane.tsx`.
- Any new page, route, or top-level surface.
- Any rewrite of a recommendation, decision, replay, backtest, risk, news, ops, policy, integration, universe, or assistant surface.

## When NOT to invoke

- Pure backend code (`backend/**/*.py`) with no UI consumer change.
- Documentation-only changes that do not touch user-facing copy.
- Build/CI plumbing.

## The ten redesign rules

1. **Decision-first.** Every workspace opens with a one-sentence answer to "what changed today and why does it matter now". Ambient widgets are secondary.
2. **Trust decomposition.** Model confidence, data confidence, and operational confidence stay three separate signals. Never collapse into one "score". The existing `ConfidenceBlock` in `frontend/src/components/recommendation/ConfidenceBlock.tsx` is the canonical primitive.
3. **Source-grounded AI.** Every AI surface ships guided prompts, source chips, retrieval freshness, and limitations. Blank-chat "ask anything" is forbidden.
4. **Readable density.** Body ≥ 15 px (default density), table text ≥ 14 px, metadata ≥ 12.5 px. The compact density mode may use 14 / 13 / 12 respectively. Never go below.
5. **Progressive disclosure for governance.** Audit trails, risk overlay rules, replay snapshots, and policy history live in drawers, not stacked on the page.
6. **Mobile becomes cards, not crushed tables.** Tables must have a card fallback below `md` (768 px). Density tweaks alone are not enough.
7. **No execution language.** "Buy", "sell", "trade", "execute", "broker", "guaranteed", "risk-free", "beat the market", "sure profit" never appear in product copy. Lint owned by `fintech-disclaimer-and-marketing-guard`.
8. **One command palette, one search.** TopBar search is reserved for the global palette (ticker / route / recommendation jump). Per-page search lives inside the page.
9. **Six product areas, not seventeen routes.** Home / Research / Decisions / Portfolio & Risk / Insights / Ops & Governance + Settings. Any new route must declare which of these six it lives in.
10. **Evidence is not optional.** Every recommendation surface includes `DisclaimerBanner` in its render tree, exposes source provenance, and shows last-updated. The `recommendation-object-provenance` and `fintech-disclaimer-and-marketing-guard` skills are co-owners of this rule.

## Forbidden patterns

- Generic SaaS admin templates (sidebar of 20 icons, every page a different table).
- "Trade now / Buy now / Execute" CTAs.
- AI sparkle icons next to a blank text box with no scaffolding.
- One-number "Smart Score" style ratings.
- 11 px metadata as the default.
- Horizontal scroll on `< md` viewports outside an explicitly opt-in desktop-only admin surface.
- Recommendation cards that do not show source / freshness / disclaimer.

## How to self-check

Before you finish a phase, ask: does the screen answer (a) what changed, (b) what needs review, (c) what evidence supports it, (d) what is stale / shadow-only / blocked? If any of those four is missing, the work is not done.

## Inputs you should already have read

- `DOCS/FINRLX_UX_UI_TRANSFORMATION_MASTER_PLAN.md`
- `DOCS/FINRLX_UX_UI_REDESIGN_PLAYBOOK.md` (Phase 1)
- `DOCS/handoff/FINRLX_UX_PHASE_0_AUDIT_REPORT.md`
- `DOCS/handoff/FINRLX_UX_PHASE_0_REDLINE_BACKLOG.md`

## Phase report obligation

Every phase report must list this skill under §B "Skills Used" and quote which of the ten rules drove which design decision.
