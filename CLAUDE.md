# FINRLX — Session Bootstrap (READ FIRST, EVERY SESSION)

> This file is auto-loaded by Claude Code at the start of every session.
> It is the **mandatory entry point** to the project's governance system.

## STOP — do this before anything else

On **every new session** (and whenever the plugin/IDE restarts), before touching any task:

1. **Read the law** → `DOCS/governance/PROJECT_RULES.md` (the 10 universal rules).
2. **Recover state** → `DOCS/governance/SESSION_STATE.md` (where the last session stopped; resume from there).
3. **Load the map** → `DOCS/governance/README.md` (how the governance files bind together).
4. Only then, act.

## The 10 rules in one breath

1. Rules live in-repo and are authoritative (`DOCS/governance/PROJECT_RULES.md`).
2. Read the rules deeply at every session start (this file forces it).
3. Keep `SESSION_STATE.md` current after **every** command and dev step — it is the crash-recovery resume point.
4. Always reply to the user in **English**.
5. For each task, assemble a **research-driven agent + skill team** matched to the work.
6. Stand up a **Council** (skeptic / QA / survey / red-team) that owns stage-gate transitions.
7. After each significant stage: **commit + push** with a detailed message.
8. At start and after each stage: show the **progress table** (✅ done / 🟡 caveats / ⬜ pending).
9. Per request: **learn from external sources → survey summary → surface questions → internal specs+tests → progress table.**
10. This whole infrastructure is file-based and tightly managed (see `README.md`).

11. **Autonomous execution** (granted 2026-07-21): the Council approves all stage transitions; do **not** stop for user approval until the whole dev process is done — except the emergency stop-conditions in `COUNCIL.md`.

## Non-negotiables (from user memory)

- **Truth-first**: no guessing, no false "done" claims. Small, verified steps. If a test fails, say so with the output.
- **Auto-push** after completing work — don't wait to be asked.
- Commit messages end with the required `Co-Authored-By` trailer.

---
_Canonical governance: `DOCS/governance/`. If this file and a governance doc disagree, the governance doc wins and this file must be updated to match._
