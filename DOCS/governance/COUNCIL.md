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
| 2026-07-21 | G4 (US-P0-06 i1 fiction-scan → ship) | ADVANCE | QA: 4 guard tests + scan deterministic; ruff/mypy PASS. Surveyor: Explore-agent inventory cross-checked by running scanner. Red Team: scan surfaced previously-unlisted ingest generators; baseline honest, no overclaim. Chair: `cb25076`. |
| 2026-07-21 | G4 (US-P0-06 i2 fail-closed → ship) | ADVANCE | QA: 46 focused + 1414 full-suite PASS. Red Team: closed a real fail-open leak (nonempty unknown source passed as real); allowlist verified against ingest branches; no regressions. Chair: `52dda91`. |
| 2026-07-21 | G4 (US-P0-06 i3 demo-labels → ship) | ADVANCE | QA: 23 focused (incl. sprint regressions) + 1418 full-suite PASS. Red Team: additive envelope label, no FE break, domain warnings intact. Chair: `ec6e944`. |
| 2026-07-21 | G4 (US-P0-07 i1 freshness-envelope → ship) | ADVANCE | QA: 13 focused + 1423 full-suite PASS; ruff/mypy clean. Red Team: closes a silent-fresh leak (meta.freshness was always null); no-data path is stale not fresh; K1 one-price-truth intact. Chair: `038e71b`. |
| 2026-07-22 | G4 (US-P0-07 i2 freshness fan-out → ship) | ADVANCE | QA: 22 focused PASS; **clean full suite 1440 passed / 2 skipped / 0 failed** (baseline 1423 + 17 new = 1440, arithmetic reconciled); `ruff check app` clean, `mypy app/core` clean; frontend 91 vitest PASS, `tsc --noEmit` clean, `next build` OK. Skeptic: an earlier run showed 5 failures — investigated, reproduced as contention between **two concurrently running suites** over the shared `research/finrlx_cpu/*.json` registries (WinError 5 on rename), all 70 PASS in isolation; not a code defect, and the clean serial run confirms it. Red Team: five surfaces could no longer be served as silently fresh; `freshness_state_from_dossier` fails closed on missing/malformed `latest_bar`; desk-status ETag now folds in staleness so a stale reading cannot hide behind a 304. Surveyor: N/A (internal wiring, no external sources needed). Chair: ADVANCE. |
| 2026-07-22 | G4 (US-P0-05 CSP / web hardening → ship) | ADVANCE | Surveyor: audited the live sites rather than the source — backend sends all 7 headers, **the browser-facing frontend sent ZERO** (no CSP, no X-Frame-Options, no HSTS). `security_headers.py` asserted "the frontend sets its own CSP via next.config.js" — that config had no `headers()` at all, so the documented control never existed. Comment corrected. QA: 8 new header tests + 99 frontend vitest PASS; `next build` exit 0; backend header tests 4 PASS; `ruff check app` clean. Red Team: **caught a self-DoS before shipping** — `headers()` is baked into `routes-manifest.json` at BUILD time, so a build without `NEXT_PUBLIC_API_BASE_URL` emitted `connect-src 'self'`, which would have blocked every browser→API call and taken the app down. Proved it empirically (built without the var, inspected the manifest), then pinned the same hardcoded fallback `src/services/api.ts` already uses, and added a regression test that builds the config with the env deleted. Also caught a build-breaking `eslint-disable` for a rule not in the project config. Skeptic: `script-src` still allows `'unsafe-inline'`/`'unsafe-eval'` (inline theme script + Next runtime) — recorded as a known, tested limitation with nonce-based hardening as the follow-up, not claimed as done. Chair: ADVANCE. |
| 2026-07-22 | G4 (US-P0-04 secure web session → ship) | ADVANCE | QA: 31 focused auth+oauth PASS; **full suite 1443 passed / 2 skipped / 0 failed** (1440 + 3 new); `ruff check app` clean; `mypy app/core` clean. Red Team: found and fixed a **latent bug** — `RefreshToken.id` is a flush-time default, so `parent.replaced_by_id = child.id` had always persisted NULL and the rotation chain was never actually linked (verified directly: id is None pre-flush). On top of that, added replay detection: presenting an already-rotated token now revokes the whole descendant chain, so a stolen token cannot keep a live session alive. Verified chain-scoped (a second device is not logged out) and cycle-safe (crafted `replaced_by_id` loop terminates). Skeptic: challenged the "HttpOnly" half of the story — migrating to cookie sessions would contradict locked Decision 2 (FE sends bearer on every call), so it is **deliberately not done** and recorded as a decision, not an omission; CSRF is structurally N/A for a bearer API, and the one cookie (Google OAuth `state`) already has HttpOnly+SameSite=Lax+state matching. Chair: ADVANCE. |
| 2026-07-22 | G4 (deploy-verification probe `/version` → ship) | ADVANCE | QA: 4 vitest PASS; builds as `ƒ (Dynamic)`, confirmed in `next build` output. Red Team: read-only, no secrets — only `RAILWAY_GIT_*` provenance already public in the repo; `no-store` prevents a cached answer defeating the probe; reports `null` rather than guessing on a half-populated env; placed outside `/api/*` so the `next.config.js` backend rewrite cannot shadow it. Chair: closes the observability gap that let a dead deploy trigger hide behind healthy 200s. |
