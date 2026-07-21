# FINRLX — Universal Project Rules (THE LAW)

**Status:** Authoritative · **Owner:** User (rotemyoeli) · **Enforced by:** Every Claude Code session
**Bootstrap:** `/CLAUDE.md` forces this file to be read at session start.

These rules override default assistant behavior. They are numbered exactly as agreed.

---

## Rule 1 — Rules are part of the repo
The universal rules live inside the project (`DOCS/governance/`), are version-controlled, and travel with the code. They are the single source of truth for how work is done here.

## Rule 2 — Read the rules first, every session
Whenever the project is opened or a new Claude Code session starts, the **first action** is to read this file (and `SESSION_STATE.md`) deeply before any task work. The root `CLAUDE.md` enforces this mechanically.

## Rule 3 — Continuous state / crash-recovery memory
`DOCS/governance/SESSION_STATE.md` is a live continuation point. It must be updated:
- after **every user command**,
- after **every meaningful development step**, and
- whenever a work-plan is produced or advanced.

If the plugin crashes or the IDE closes, the next session reads `SESSION_STATE.md` **first** and resumes exactly where work stopped. Treat it as an append-and-refresh log, never let it go stale.

## Rule 4 — English only
All assistant prose, commit messages, and documents are written in **English**, regardless of the language of the user's request.

## Rule 5 — Research-driven agent + skill team per task
Before leading any development effort, analyze the task and **assemble a fit-for-purpose team** of agents and skills, chosen from a deliberate mapping of available agent technologies and skills (see `AGENT_TEAM.md`). This selection step is mandatory and is documented per task.

## Rule 6 — The Council (doubt / QA / survey / red-team)
Stand up a **Council** of agents responsible for challenge, testing, review, and adversarial ("red team") scrutiny of every process led here. The Council **owns the transitions between stages** — no stage advances without its gate. Charter in `COUNCIL.md`.

## Rule 7 — Commit + push after every significant stage
After each significant development stage: create a commit with a **detailed** message documenting what changed and why, and **push** it. Do not wait to be asked.

## Rule 8 — Progress table at start and after each stage
At the start of a development process and after each significant stage, present a **task/stage progress table** using:
- ✅ (green V) — stage completed,
- 🟡 — completed/blocked **with reservations** the user must know about (with a note),
- ⬜ — not started / pending.
The live table lives in `PROGRESS.md`.

## Rule 9 — Standard operating procedure per request
For each request, follow the pipeline (detailed in `WORKFLOW.md`):
1. Analyze the request.
2. **Learn from external sources** (relevant forums, Git repos) matched to the task context.
3. Produce a **survey summary** and **surface questions** to the user when needed.
4. Produce **internal specification documents** — development plans and test plans — co-authored with the matched agents, skills, and Council.
5. Present the **progress-stages table**.

## Rule 10 — File-based, tightly managed infrastructure
This entire governance system is built at the file / Markdown level. Its structure and management method are documented in `DOCS/governance/README.md`. Development proceeds only after this infrastructure is in place.

## Rule 11 — Autonomous, Council-governed execution (granted 2026-07-21)
The **Council owns all stage-transition approvals**. No per-stage approval from the user is required. Once a development process is underway, **do not stop** until the entire process is complete — running each slice `research → implement → verify → Council gate → commit+push → next` continuously. Prefer a safe, reversible default over pausing. The **only** permitted stops are the emergency stop-conditions in `COUNCIL.md` ("Emergency stop-conditions"). This rule does not weaken truth-first (Rule elsewhere / user memory): the Council still may not advance on unverified or overstated claims.

---

### Precedence
User's explicit in-session instruction > these Rules > `CLAUDE.md` summary > default behavior.
When any conflict is found, the higher-precedence source wins and the lower-precedence file is corrected to match.
