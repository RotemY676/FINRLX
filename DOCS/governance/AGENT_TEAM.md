# FINRLX — Agent & Skill Team (Rule 5)

**Purpose:** For every development effort, assemble a fit-for-purpose team of agents and skills,
selected by deliberate analysis of the task — not by default. This file defines *how* the team is
chosen and records the standing roster.

---

## Selection method (run this per task)

1. **Classify the task** along dimensions: backend / frontend / data-ML / security / infra-ops / docs / research / UX.
2. **Decompose** into independent sub-workstreams that can be scouted or built in parallel.
3. **Map agents** — pick the narrowest capable agent type per sub-workstream:
   - `Explore` — read-only fan-out search across many files (locate, don't audit).
   - `Plan` — architecture / implementation strategy, no edits.
   - `general-purpose` / `claude` — multi-step build & investigation.
   - Specialist subagents (e.g. `code-reviewer`, `Explore`) when a sharper lens helps.
4. **Map skills** — match the task to concrete skills already installed for this repo (see roster) and to the global skill catalog (security, testing, backend, frontend, data). Prefer project-local skills first.
5. **Record the chosen team** in the task's plan and in `SESSION_STATE.md`. State *why* each was picked.
6. **Right-size parallelism** — independent scouts/builders run concurrently; dependent steps run in sequence.

## Standing roster — project-local skills (`.claude/skills/`)

These FINRLX skills are the first-choice tools; map tasks to them before reaching for generic ones:

| Skill | Use for |
|---|---|
| `finrlx-ai-ux-governance` | AI/UX governance guardrails on product surfaces |
| `finrlx-fintech-dashboard-patterns` | Dashboard/data-viz patterns |
| `finrlx-home-command-center` | Home / command-center surface work |
| `finrlx-ux-redesign-director` | UX/UI redesign direction |
| `finrlx-visual-qa-accessibility-gate` | Visual QA + accessibility gating |
| `finrlx-handoff-evidence-packager` | Packaging handoff/evidence artifacts |
| `backtest-hygiene-gate` | Backtest correctness / leakage hygiene |
| `replay-determinism-harness` | Deterministic replay verification |
| `recommendation-object-provenance` | Provenance of recommendation objects |
| `feature-flag-kill-switch` | Feature-flag / kill-switch discipline |
| `fintech-disclaimer-and-marketing-guard` | Compliance disclaimers / marketing guard |
| `anthropic-frontend-design-mirror`, `vercel-web-design-guidelines-mirror` | Frontend design guideline mirrors |

## Standing roster — common global skills by task type

- **Backend/API:** `backend-architect`, `fastapi-pro`, `api-security-testing`, `python-testing-patterns`.
- **Security/Ops:** `security-auditor`, `api-security-best-practices`, `pentest-checklist`, `secrets-management`.
- **Frontend/UX:** `frontend-design`, `react-best-practices`, `accessibility-compliance-accessibility-audit`.
- **Data/ML/quant:** `quant-analyst`, `backtesting-frameworks`, `data-quality-frameworks`, `ml-engineer`.
- **Review/verify:** `code-reviewer`, `verification-before-completion`, `adversarial-audit` (feeds the Council).

> The global catalog is large; this list is the shortlist. Always confirm a skill exists in the
> available-skills list before invoking it, and prefer the project-local skill when both apply.

## Team record (append per task)

| Date | Task | Agents chosen | Skills chosen | Rationale |
|---|---|---|---|---|
| 2026-07-21 | Governance bootstrap | direct (single-context authoring) | — | Meta/setup task; small, sequential, no fan-out warranted. |
