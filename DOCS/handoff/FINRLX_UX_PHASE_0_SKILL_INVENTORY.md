# FINRLX UX/UI Transformation — Phase 0 Skill Inventory

> Required by `DOCS/FINRLX_UX_UI_TRANSFORMATION_MASTER_PLAN.md` §1.2. This file
> documents what skills already exist in the FINRLX repo, which were created
> during Phase 0, and which the plan calls for but are still missing. It is
> the source of truth for "what we can rely on" before Phase 1 begins
> installing/creating the redesign skill layer.

Search performed (PowerShell):

```powershell
Get-ChildItem -Recurse -Filter SKILL.md -ErrorAction SilentlyContinue | Select-Object FullName
Get-ChildItem -Recurse -Directory -Filter skills -ErrorAction SilentlyContinue | Select-Object FullName
```

POSIX equivalent (also run):

```bash
find . -maxdepth 6 -type f -iname SKILL.md
```

Results were filtered to exclude `frontend/node_modules/**` (Playwright ships
unrelated SKILL.md files inside `playwright-core`).

## 1. Project-local skills present in `.claude/skills/`

| Skill folder | `name` (frontmatter) | Plan §1.3 row | Status | Notes |
|---|---|---|---|---|
| `.claude/skills/backtest-hygiene-gate/` | `backtest-hygiene-gate` | Yes | Present | CI gate for look-ahead bias, OOS split, Sharpe, rebalance count, outliers. Should fire in Phases 6 and 12 if backtest UI is touched. |
| `.claude/skills/feature-flag-kill-switch/` | `feature-flag-kill-switch` | Yes | Present | Maps to `FeatureFlagsContext` + `/api/v1/flags`. Must fire on every new top-level route in Phases 2 and 4. |
| `.claude/skills/fintech-disclaimer-and-marketing-guard/` | `fintech-disclaimer-and-marketing-guard` | Yes | Present | Lints forbidden verbs and verifies `DisclaimerBanner` lives in every recommendation render path. Must fire in every phase that ships copy (≥ Phase 3). |
| `.claude/skills/recommendation-object-provenance/` | `recommendation-object-provenance` | Yes | Present | Enforces tamper-evident, replayable recommendation objects. Relevant to Phases 5, 7, 11. |
| `.claude/skills/replay-determinism-harness/` | `replay-determinism-harness` | Yes | Present | Locks the byte-identical replay-snapshot contract. Relevant to Phase 7 and Phase 12. |
| `.claude/skills/finrlx-home-command-center/` | `finrlx-home-command-center` | Not listed in plan §1.3 | Present (added during Phase HOME-1 prior to this plan) | Page-scoped — encodes the home `/` UX contract. Useful precedent for the structure of the five Phase-1 skills, but does **not** substitute for them. |

**Skills present: 6.** All five skills that the plan §1.3 expects to exist
are present. No gaps in the pre-existing safety layer.

## 2. Project-local skills the plan §1.5 requires Claude to create — all missing

The master plan §1.5 lists five new project-local skills that govern the
redesign program. None of them exist yet. They are required deliverables of
Phase 1 — not Phase 0 — so this is recorded as a known gap, not a Phase 0
defect.

| Required skill (per plan §1.5) | Expected path | Phase that needs it most | Status |
|---|---|---|---|
| `finrlx-ux-redesign-director` | `.claude/skills/finrlx-ux-redesign-director/SKILL.md` | All redesign phases (2–11) | **Missing — to create in Phase 1** |
| `finrlx-fintech-dashboard-patterns` | `.claude/skills/finrlx-fintech-dashboard-patterns/SKILL.md` | Phases 5, 6, 8, 9 | **Missing — to create in Phase 1** |
| `finrlx-ai-ux-governance` | `.claude/skills/finrlx-ai-ux-governance/SKILL.md` | Phases 6, 11 | **Missing — to create in Phase 1** |
| `finrlx-visual-qa-accessibility-gate` | `.claude/skills/finrlx-visual-qa-accessibility-gate/SKILL.md` | End of every phase ≥ 3 | **Missing — to create in Phase 1** |
| `finrlx-handoff-evidence-packager` | `.claude/skills/finrlx-handoff-evidence-packager/SKILL.md` | End of every phase | **Missing — to create in Phase 1** |

Phase 0 does **not** create any of these — that is explicitly Phase 1 work
(see plan §5 Phase 1 "Skill setup and FINRLX redesign playbook"). Phase 0
also does not touch the existing 6 skills.

## 3. External skills the plan §1.4 lists — none installed in repo

A repo-wide search confirms there is no `node_modules/@anthropics/skills`,
no `node_modules/@vercel/agent-skills`, no `node_modules/skills`, and no
local mirror of the Anthropic or Vercel agent-skill packages under
`.claude/external-skills/`. The Anthropic `frontend-design` skill and the
Vercel `web-design-guidelines` skill have **not** been installed or mirrored
locally. The plan allows either an `npx skills add …` install **or** a
documented manual mirror; both decisions are deferred to Phase 1, after
auditing each skill's content for safety (plan §1.4-B explicitly warns
against blind remote install).

| External skill | Plan recommendation | Action taken in Phase 0 | Next step |
|---|---|---|---|
| Anthropic `frontend-design` (`anthropics/skills`) | Recommended for Phases 3–8 | Reviewed link only — not fetched | Phase 1: audit and install or mirror as `.claude/skills/anthropic-frontend-design-mirror/SKILL.md`. |
| Vercel `web-design-guidelines` (`vercel-labs/agent-skills`) | Audit before use | Reviewed link only — not fetched | Phase 1: audit content. If safe, mirror locally; if not, copy only a vetted subset. |
| shadcn/ui (component library) | Use carefully, do not blindly install | Not installed | Phase 3: decide per-primitive whether to adopt a shadcn pattern or extend existing `frontend/src/components/ui/**`. |
| Vercel AI Elements / AI SDK UI | Evaluate only for AI assistant surfaces | Not installed | Phase 11: re-evaluate when the research assistant gets its own UX redesign. |

## 4. Other SKILL.md files found on disk (ignored)

- `frontend/node_modules/playwright-core/lib/tools/cli-client/skill/SKILL.md`
- `frontend/node_modules/playwright-core/lib/tools/trace/SKILL.md`

These are Playwright-internal and are unrelated to FINRLX. They are listed
here only so the inventory is verifiably complete; they do not influence
the redesign.

## 5. Security review of the skill inventory

- All 6 project-local skills are FINRLX-authored and live under
  `.claude/skills/` in source control. None reach out to remote resources at
  load time.
- The frontmatter for each existing skill uses either `type: project` or
  `source: project`. Both styles are accepted by the skill loader; Phase 1
  should normalize them to `type: project` for consistency.
- No untrusted external skill has been installed or fetched in Phase 0.

## 6. Phase 0 conclusion on the skill layer

The existing five governance skills (`backtest-hygiene-gate`,
`feature-flag-kill-switch`, `fintech-disclaimer-and-marketing-guard`,
`recommendation-object-provenance`, `replay-determinism-harness`) are
sufficient to keep the redesign program safe through Phase 1. The five new
redesign skills the plan calls for in §1.5 are still missing and are the
primary deliverable of Phase 1. No skill creation was performed in Phase 0.
