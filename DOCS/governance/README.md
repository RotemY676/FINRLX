# FINRLX Governance — Structure & Management Map (Rule 10)

This directory is the **operating system** for how work is done in FINRLX. It is file-based,
version-controlled, and tightly bound so that any session (or a fresh one after a crash) behaves
consistently.

## Files and their jobs

```
/CLAUDE.md                        ← auto-loaded EVERY session; forces reading the rules first (Rule 2)
DOCS/governance/
├── README.md                     ← THIS FILE — the map (Rule 10)
├── PROJECT_RULES.md              ← the 10 universal rules, authoritative (Rule 1)
├── SESSION_STATE.md              ← live crash-recovery resume point (Rule 3)
├── AGENT_TEAM.md                 ← how the agent+skill team is chosen per task (Rule 5)
├── COUNCIL.md                    ← skeptic/QA/survey/red-team; owns stage gates (Rule 6)
├── WORKFLOW.md                   ← the SOP pipeline + commit/push discipline (Rules 7,8,9)
└── PROGRESS.md                   ← live task/stage progress table (Rule 8)
```

## How the pieces bind together (the control loop)

```
 New session ── reads ──▶ CLAUDE.md ──▶ PROJECT_RULES.md + SESSION_STATE.md
       │                                          │
       ▼                                          ▼
  New request ──▶ WORKFLOW.md pipeline ──▶ AGENT_TEAM.md (assemble team)
       │                                          │
       ▼                                          ▼
   each stage ◀── gated by ── COUNCIL.md ──▶ updates PROGRESS.md + SESSION_STATE.md
       │
       ▼
   ship (commit+push) ──▶ report progress table to user
```

## Management guarantees

- **Always-on entry:** root `CLAUDE.md` is auto-loaded, so Rule 2 cannot be skipped.
- **Never lose your place:** `SESSION_STATE.md` is updated after every command/step (Rule 3); a fresh session resumes from it. It supersedes the legacy root `RESUME.md`.
- **No silent stage jumps:** the Council (`COUNCIL.md`) gates every transition and logs the verdict.
- **Team is deliberate, not default:** `AGENT_TEAM.md` records which agents/skills were chosen and why (Rule 5).
- **Visible truth:** `PROGRESS.md` shows ✅/🟡/⏳/⬜ at start and after each stage (Rule 8); commits+pushes document each stage (Rule 7).
- **Language:** all outputs in English (Rule 4).

## When you change how work is done
1. Edit the relevant governance file (rules → `PROJECT_RULES.md`, process → `WORKFLOW.md`, etc.).
2. Reflect the change in `CLAUDE.md`'s summary if it affects session bootstrap.
3. Commit + push with a message explaining the governance change.
4. Note it in `SESSION_STATE.md`.

## Relationship to existing project docs
- `DOCS/specs/` — product/technical/QA specs of record (SPEC-00..04). Governance references them; does not replace them.
- `DOCS/implementation/`, `DOCS/working_docs/`, `DOCS/handoff/` — plans, working notes, handoffs. Governance's SOP writes new plans here.
- Root `RESUME.md` — legacy resume note; kept for history, but `SESSION_STATE.md` is now authoritative.
