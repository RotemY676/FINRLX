# FINRLX — Standard Operating Procedure (Rules 7, 8, 9)

**Purpose:** The repeatable pipeline every request runs through, and the discipline for shipping.

---

## The pipeline

```
0. INTAKE      Analyze the request. Restate scope. Assemble the agent+skill team (AGENT_TEAM.md).
1. RESEARCH    Learn from external sources matched to the task: relevant forums, Git repos, docs.
2. SURVEY      Write a survey summary of findings. Surface open QUESTIONS to the user where needed.
   └─ GATE G0/G1 (Council)
3. SPEC        Author internal specs: requirements, development plan, and TEST plan.
               Co-author with matched agents/skills + Council.
   └─ GATE G2 (Council)
4. BUILD       Implement in small, verified steps. Keep SESSION_STATE.md updated throughout.
   └─ GATE G3 (Council)
5. VERIFY      Run tests. Report real output. Truth-first: failures are stated plainly.
   └─ GATE G4 (Council)
6. SHIP        Commit + push with a detailed message. Update PROGRESS.md + SESSION_STATE.md.
7. REPORT      Present the progress table to the user.
```

Scale the pipeline to the task: a one-line doc fix does INTAKE→BUILD→SHIP with a light gate;
a security/data/ML change runs the full pipeline with the full Council.

## Rule 9 — deliverables per request
- **Survey summary** (from stage 2): what was learned externally, with source pointers.
- **Questions to user** (from stage 2): anything ambiguous, blocking, or a real decision.
- **Internal spec docs** (from stage 3): dev plan + test plan, stored under `DOCS/` (specs in `DOCS/specs/`, plans in `DOCS/implementation/` or `DOCS/working_docs/`).
- **Progress table** (stage 7): updated `PROGRESS.md`.

## Rule 7 — commit + push discipline
After each significant stage:
1. Stage only the intended files (`git status` first; never sweep unrelated changes).
2. Commit with a detailed message: **what** changed, **why**, and **which stage/gate** it closes.
3. If on `main`, prefer a branch when the change is substantial; otherwise commit per user's established `main` workflow.
4. **Push.** Do not wait to be asked (user memory: auto-push).
5. Commit message ends with the required trailer:
   `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`

## Rule 8 — progress table format
Maintained in `PROGRESS.md`; echoed to the user at start and after each stage.

| Legend | Meaning |
|---|---|
| ✅ | Stage complete (green V) |
| 🟡 | Complete/blocked **with reservations** — note is mandatory |
| ⬜ | Pending / not started |
| ⏳ | In progress |

Columns: `Stage / Task · Owner (agent) · Gate · Status · Notes`.

## Truth-first guardrails (user memory — always on)
- No guessing and no unverified "done."
- Small steps, each verified before the next.
- If a test fails, show the output and say so. If a step was skipped, say it was skipped.
