# FINRLX UX/UI Redesign Playbook

> Required by `DOCS/FINRLX_UX_UI_TRANSFORMATION_MASTER_PLAN.md` §5 Phase 1.
> The playbook is the canonical reference every later phase reads before it
> writes code. It is intentionally concise. If a rule is not here, it is not
> a rule.

**Audience.** Anyone making UI changes to FINRLX — engineers, designers,
agent (Claude Code, Anthropic). Read once before starting work in a phase,
re-read before opening a PR.

**Last reviewed.** 2026-05-22, end of Phase 1.

---

## 1. The four questions every screen must answer

In ≤ 5 seconds of looking at any FINRLX page, the user must be able to
answer all four:

1. **What changed?** (since last visit / since last refresh)
2. **What requires my review?**
3. **What evidence supports the items I'm seeing?**
4. **What is stale, shadow-only, or blocked?**

If a page does not answer all four, it is not done.

---

## 2. Product architecture — the six areas

Every route belongs to exactly one of these six product areas, plus
Settings.

| Area | Top-level path | Purpose |
|---|---|---|
| Home / Command Center | `/` | Triage; answers the four questions above. |
| Research | `/research/**`, `/universe` | Ticker / company / sector / theme research. |
| Decisions | `/decision`, `/decision/:id`, `/comparison`, `/replay`, `/templates` | Recommendation lifecycle, comparison, forensics. |
| Portfolio & Risk | `/paper`, `/risk` | Exposure, risk metrics, scenario stress. |
| Insights | `/news` | Decision-linked research events, not generic news. |
| Ops & Governance | `/ops`, `/policies`, `/integrations`, `/admin`, `/operator` | System health, gates, audit. |
| Settings | `/profile`, `/help`, account | Personal preferences and help. |

New routes that do not fit one of these are not allowed without an explicit
playbook update.

---

## 3. Design vocabulary

### Components (reuse these — don't duplicate)

| Pattern | Component |
|---|---|
| Confidence trio | `frontend/src/components/recommendation/ConfidenceBlock.tsx` |
| Recommendation card | `frontend/src/components/recommendation/RecommendationCard.tsx` |
| Status pill | `frontend/src/components/recommendation/StatusBadge.tsx` |
| Source provenance | `frontend/src/components/recommendation/SourceBadge.tsx` |
| Weights table | `frontend/src/components/recommendation/WeightsTable.tsx` |
| Warnings | `frontend/src/components/recommendation/WarningsBlock.tsx` |
| Freshness chip | `frontend/src/components/home/DataFreshnessBadge.tsx` |
| Loading | `frontend/src/components/feedback/PageLoading.tsx` |
| Empty | `frontend/src/components/feedback/PageEmpty.tsx` |
| Error | `frontend/src/components/feedback/PageError.tsx` |
| Skeleton | `frontend/src/components/feedback/Skeleton.tsx` |
| Disclaimer (every recommendation surface) | `frontend/src/components/legal/DisclaimerBanner.tsx` |
| App shell | `frontend/src/components/shell/AppShell.tsx` |
| Context pane | `frontend/src/components/shell/ContextPane.tsx` |
| Help link in-line | `frontend/src/components/help/HelpLink.tsx` |

### Tokens

- Live in `frontend/src/app/globals.css` (`:root` and `:root[data-theme="dark"]`).
- Surfaced into Tailwind via `frontend/tailwind.config.ts`.
- Original token ledger: `design/handoff-package/handoff-package/tokens.css`.

### Typography scale (Phase 3 target)

| Element | Default density | Compact | Comfortable |
|---|---:|---:|---:|
| Page title | 28 px | 24 px | 32 px |
| Section title | 20 px | 18 px | 22 px |
| Card title | 16 px | 15 px | 17 px |
| Body | 15 px | 14 px | 16 px |
| Table body | 14 px | 13 px | 15 px |
| Metadata / caption | 12.5 px (minimum) | 12 px | 13.5 px |
| Buttons | 14 px | 13 px | 15 px |

These are *targets*. Phase 3 sets them; later phases must not regress.

### Density modes

`<html data-density="compact|default|comfortable">`. The default density
is the canonical typography. Per-table density opt-in is allowed; never
override globally without an explicit playbook update.

### Color tokens (existing + Phase 3 additions)

Existing semantic palette in `globals.css`:
- `pos` / `pos-soft` / `pos-soft-ink` — positive, fresh, approved.
- `caution` / `caution-soft` / `caution-soft-ink` — warning, stale, partial.
- `breach` / `breach-soft` / `breach-soft-ink` — blocked, error, policy violation.
- `primary` / `primary-soft` / `primary-soft-ink` — active / navigational / current.
- `accent` / `accent-2` — research-only, model-comparison, shadow lanes.

Phase 3 introduces:
- `stale` (visual alias of `caution-soft` with a "stale" semantic tag).
- `shadow-only` (visual alias of `accent-2-soft`).
- `blocked` (visual alias of `breach-soft`).
- `governance` (a calm institutional `primary-soft` variant).

These will not introduce new hues — only named semantic aliases.

---

## 4. Forbidden language

Never appears in product copy (UI or marketing):

- "Buy now", "sell now", "trade now"
- "Execute trade", "place trade", "broker"
- "Guaranteed return", "risk-free", "sure profit"
- "Beat the market", "always wins", "AI-picked"

`fintech-disclaimer-and-marketing-guard` enforces the list. Phase 12 runs
`rg` over `frontend`, `DOCS`, and `backend` as a gate check.

## 5. Forbidden UI patterns

- Generic SaaS admin templates (20-icon sidebar; every page a different table).
- Blank "ask anything" AI input with no scaffolding.
- One-number "Smart Score" tiles.
- Body text < 14 px.
- Horizontal scroll on `< md` viewports outside an opt-in desktop-only admin surface.
- Recommendation cards without source / freshness / disclaimer.
- "Trade now / Buy now / Execute" buttons.

## 6. Mandatory rules for every data component

- `asOf`, `status`, `source`, `unit`, optional `delta`, and `freshnessLabel`.
- Loading / empty / error / stale / shadow-only / partial states.
- Tables become cards below `md`.
- Numeric columns use tabular figures.
- All status pills carry both a color and a word.

## 7. Required AI guardrails

- Guided prompts on every assistant surface.
- Source chips with freshness on every answer.
- Retrieval state: `retrieved | partial | model-only` (model-only carries caution).
- One-line limitations footer.
- "Open evidence" action on every answer.

## 8. Phase report contract

Every phase report follows the master plan §6 template. Section B must
list which skills were consulted, and §J must list known limitations
honestly. A phase whose §J is empty is suspect.

## 9. Gate skills

| Skill | When |
|---|---|
| `finrlx-ux-redesign-director` | Before every phase |
| `finrlx-fintech-dashboard-patterns` | Before component / page work |
| `finrlx-ai-ux-governance` | Before any AI / RL / assistant surface |
| `finrlx-visual-qa-accessibility-gate` | After every phase ≥ 3 |
| `finrlx-handoff-evidence-packager` | At the close of every phase |
| `anthropic-frontend-design-mirror` | For design taste decisions in Phase 3 + 5–9 |
| `vercel-web-design-guidelines-mirror` | For per-file UI audits in Phase 3 + 12 |
| `fintech-disclaimer-and-marketing-guard` | Before shipping any copy |
| `recommendation-object-provenance` | Before changing any decision / replay / recommendation surface |
| `backtest-hygiene-gate` | Before any backtest / RL UI |
| `replay-determinism-harness` | Before any replay UI |
| `feature-flag-kill-switch` | Before adding any new surface |

## 10. Open questions tracked across phases

These are unanswered as of end of Phase 1. They become Phase-2 inputs.

1. Should `/decision` (current) and `/decision/:id` (specific) be merged or kept distinct? — Tentative answer: keep distinct, `/decision` is a redirect to the latest. Confirm in Phase 2 IA.
2. Is `/comparison` a route or an in-page tab on Decision? — Tentative: in-page tab; preserve route as redirect.
3. Is `/operator` user-visible or operator-only? — Tentative: operator-only behind `operator_console` flag, surfaced from Ops & Governance.
4. Should the command palette be a Phase 4 deliverable or deferred? — Tentative: Phase 4. It is what makes navigation finally feel coherent.
5. What is the canonical naming for "shadow-only research lane"? — Candidates: "Research-only", "Shadow", "Shadow research", "Lab". Phase 3 to lock.

These will be resolved before the relevant later phase opens.
