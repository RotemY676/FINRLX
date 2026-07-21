# FINRLX — The Council (Rule 6)

**Purpose:** A standing panel of adversarial/quality roles that challenges every process and **owns
the transitions between stages**. No stage advances to the next without passing its gate.

---

## Council seats (roles, not necessarily distinct agents)

| Seat | Mandate | Typical agent/skill |
|---|---|---|
| **Skeptic** | Cast doubt on assumptions, claims, and "done" statements. Demand evidence. | `Plan` / `adversarial-audit` |
| **QA / Test** | Verify behavior against spec; require passing tests + real output. | `code-reviewer`, `verification-before-completion`, `python-testing-patterns` |
| **Surveyor** | Confirm external-source research was done and is sound (Rule 9). | `Explore`, `deep-research` |
| **Red Team** | Attack the change: security, abuse, edge cases, regressions, leakage. | `security-auditor`, `pentest-checklist`, `backtest-hygiene-gate` |
| **Chair** | Weighs the votes, records the verdict, authorizes the stage transition. | lead (this session) |

## Stage gates (the Council decides transitions)

The standard pipeline (see `WORKFLOW.md`) is:
`Research → Survey+Questions → Spec/Plan/Tests → Build → Verify → Ship (commit+push)`

Between each pair of stages, the Council runs a gate:

- **G0 Research→Survey:** external sources actually consulted and relevant? (Surveyor)
- **G1 Survey→Spec:** open questions surfaced to user and resolved/parked? (Skeptic + Chair)
- **G2 Spec→Build:** spec + test plan concrete, testable, scoped? (QA + Skeptic)
- **G3 Build→Verify:** change complete, no obvious regressions? (QA)
- **G4 Verify→Ship:** tests pass with real output; Red Team found no blocker; truth-first claim holds? (Red Team + QA + Chair)

## Gate verdict format (record in PROGRESS.md / SESSION_STATE.md)

```
GATE Gx — <stage transition>
  Skeptic:  PASS | CONCERN — <note>
  QA:       PASS | FAIL   — <evidence / test output>
  Surveyor: PASS | N/A    — <sources>
  Red Team: PASS | BLOCK  — <finding>
  Chair verdict: ADVANCE | HOLD — <reason>
```

## Autonomous authority (granted 2026-07-21)

The Council has **full authority to approve stage transitions without user sign-off** (Rule 11).
The lead does **not** pause for routine confirmation and does **not** halt the development process
until it is complete. Every gate is still run and logged; the Chair records the verdict and advances.

### Emergency stop-conditions (the ONLY reasons to pause and ask the user)
1. **Credentials / secrets** are required, or an action would expose secrets/tokens/keys.
2. **Destructive or irreversible** action: `git reset --hard`, force-push, production deploy,
   data deletion/migration of real data, merging via external systems, or **any** real-money /
   live-trading / broker-execution enablement.
3. A **genuine blocker** with no safe workaround (e.g. an unresolvable conflict, a hard external
   dependency failure) that prevents further progress.
4. A **material product decision** that cannot be safely defaulted. Even here, prefer a safe,
   reversible default + documentation and keep going; stop only if the choice is truly irreducible.
5. A **financial-truth violation** that cannot be satisfied fail-closed.

Anything outside this list: the Council decides and execution continues.

## Rules of order
- A **BLOCK** from Red Team or a **FAIL** from QA halts the transition until resolved.
- Truth-first (user memory): the Chair may not record ADVANCE on unverified or overstated claims.
- Every gate verdict is logged so a fresh session can see why a stage advanced.
- Scale the ceremony to the task: trivial mechanical edits get a lightweight single-Chair gate;
  security/data/ML changes get the full panel.

## Log (append per gate)

| Date | Gate | Verdict | Note |
|---|---|---|---|
| 2026-07-21 | G4 (governance bootstrap → ship) | ADVANCE | Files authored & internally consistent; low-risk docs change. Commit+push authorized. |
| 2026-07-21 | G4 (US-P0-03 i2 ingest-authz → ship) | ADVANCE | QA: 39 focused + 1394 full-suite PASS (real output). Ruff/mypy PASS. Red Team: strengthens zero-fiction control (blocks anon market-data write), adds negative 401 test + ledger ratchet; no BLOCK. Chair: commit `28b8bf6` pushed. |
