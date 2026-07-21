# FINRLX — SESSION STATE (Crash-Recovery Resume Point)

> **Rule 3.** This is the live continuation memory. On any restart, read this FIRST.
> Update it after every user command and every meaningful dev step. Never let it go stale.
> Times are absolute (project date reference: 2026-07-21).

---

## 🔴 RESUME HERE (most recent first)

### Entry — 2026-07-21 · Governance infrastructure bootstrap
- **User request:** Build the universal project-rules file + crash-recovery memory file + agent-team + council + workflow + progress-table infrastructure (10 rules), show the structure, then continue development.
- **What was done:**
  - Created `/CLAUDE.md` (session bootstrap that forces reading the rules first).
  - Created `DOCS/governance/`: `PROJECT_RULES.md`, `SESSION_STATE.md` (this file), `AGENT_TEAM.md`, `COUNCIL.md`, `WORKFLOW.md`, `PROGRESS.md`, `README.md`.
- **State:** Governance layer authored, committed (`79f5621`), and pushed to `main`. Structure presented to user. Awaiting user's choice of next development track.
- **Next action for a fresh session:** Ask the user which track to resume (see "Open threads" below). Do NOT auto-commit the inherited P0 working-tree changes without user review.

---

## Current development context (inherited, pre-governance)

Source of truth before this file existed: root `RESUME.md` + git log. Summary:
- **Program LEAP** Plan v4.0 + Track B "Operation One Desk". F0–S9, A1–A6, K1(1–3) COMPLETE on `main`.
- **Desk W1 build** COMPLETE for structural scope (behind `FEATURE_DESK_V2`, flag OFF).
- Recent `main` commits center on **P0 security/ops user stories**: US-P0-01 (runtime inventory manifest), US-P0-03 (route authorization + governance-mutation auth), US-P0-08 (readiness endpoint + jobs component).
- **Uncommitted at governance-setup time** (do not lose): modifications to `ingest.py`, `route_policy.py`, several tests, registries; new file `backend/tests/test_p0_ingest_authz.py`.

## Open threads / next candidate work
- P0 track continuation (US-P0-xx security/ops hardening) — has uncommitted changes in the working tree.
- Browser phase per `DOCS/handoff/CLAUDE_CODE_HANDOFF_DESK_W1.md` (e2e matrix, screenshots, exit gates G-1..G-7, then flip `FEATURE_DESK_V2`).
- Operator items: E1 (rotate PAT — treat as compromised), E7 (torch worker), E8 (Finnhub social tier).

## Known caveats to carry forward
- 🟡 The working tree had **uncommitted P0 changes** when the governance layer was added. These are unrelated to governance and must be reviewed/committed separately with the user.
- 🟡 A stray Hebrew-named `.docx` at repo root ("טבלת שלבי הפיתוח...") is the legacy dev-stages table; `PROGRESS.md` supersedes it as the live table.

---

## How to update this file (checklist)
1. Prepend a new dated entry under **RESUME HERE** (most recent first).
2. State: request → actions taken → current state → explicit next action.
3. Move anything still pending into **Open threads**.
4. Record new caveats. Keep the file readable — trim entries older than the current milestone into a short rollup.
