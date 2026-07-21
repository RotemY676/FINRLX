# FINRLX — Live Progress Table (Rule 8)

**Legend:** ✅ done · 🟡 done/blocked with reservations (see note) · ⏳ in progress · ⬜ pending
**Updated:** 2026-07-21

---

## Track 0 — Governance infrastructure bootstrap (this request)

| # | Stage / Task | Owner | Gate | Status | Notes |
|---|---|---|---|---|---|
| 0.1 | Inspect repo conventions (DOCS, RESUME, skills) | lead | — | ✅ | No `CLAUDE.md` existed; `DOCS/` is docs home. |
| 0.2 | Root `CLAUDE.md` bootstrap (forces Rule 2) | lead | — | ✅ | Auto-loaded each session. |
| 0.3 | `PROJECT_RULES.md` (the 10 rules) | lead | — | ✅ | Authoritative law file. |
| 0.4 | `SESSION_STATE.md` (crash-recovery memory, Rule 3) | lead | — | ✅ | Live resume point. |
| 0.5 | `AGENT_TEAM.md` (Rule 5) | lead | — | ✅ | Selection method + roster. |
| 0.6 | `COUNCIL.md` (Rule 6) | lead | — | ✅ | Seats + stage gates G0–G4. |
| 0.7 | `WORKFLOW.md` (Rules 7–9 SOP) | lead | — | ✅ | Pipeline + push discipline. |
| 0.8 | `PROGRESS.md` (this table, Rule 8) | lead | — | ✅ | Live table. |
| 0.9 | `README.md` (structure map, Rule 10) | lead | — | ✅ | How it all binds. |
| 0.10 | Commit + push governance layer (Rule 7) | lead | G4 | ✅ | Commit `79f5621` pushed to `main`. |
| 0.11 | Present structure to user, confirm, resume dev | lead | — | ⏳ | Structure presented; awaiting user go-ahead on next track. |

## Track DPK/P1 — DecisionPacket truth-gate (delivered by crashed session, verified on `main`)

| # | Task | Gate | Status | Notes |
|---|---|---|---|---|
| DPK-baseline | Runtime + truth baseline docs (ADR-0001, DELTA, STATUS) | — | ✅ | `bb7b9cb`. |
| DPK-contract | Canonical packet schema + `decision_truth.py` policy | — | ✅ | `1772551` (candidate ZIP adapted to repo conventions). |
| DPK-integrate | Feature-flagged (`decision_packet_v1`, OFF) adapter + API | — | ✅ | `eb03555`. Read-only seam; legacy paths intact. |
| DPK-tests | Fail-closed evidence policy tests (P1 adapter+API) | — | ✅ | `c7fd0dd`. |

## Track P0 — Security/Ops hardening (inherited + this session)

| # | Task | Gate | Status | Notes |
|---|---|---|---|---|
| P0-01 | Runtime inventory manifest (admin-only) | — | ✅ | On `main` (cff56c5). |
| P0-03 i0 | Route authorization matrix + audit ratchet | — | ✅ | On `main` (a8633f3). |
| P0-03 i1 | Auth-gate publication governance mutations (5) | — | ✅ | On `main` (20483af). |
| P0-03 i2 | Auth-gate market-data ingestion (bars/news) | G4 | ✅ | **This session** `28b8bf6`. 39 focused + 1394 full suite green; ruff/mypy clean. Debt 194→192. |
| P0-08 | Unified readiness endpoint + jobs component | — | ✅ | On `main` (e3ba39a, d1a772d). |

## Remaining P0 work (priority order, from STATUS doc)
- ⬜ **US-P0-03 continued** — gate remaining auth-debt (192): pipeline/engines/features deferred (heavy test-fixture use); needs beta auth-model decision (does FE send a bearer on every call?).
- ⬜ **US-P0-06** — zero-fiction *static scan* across production paths (beyond the adapter classifier).
- ⬜ **US-P0-04** — secure web session (HttpOnly / rotation / CSRF E2E).
- ⬜ **US-P0-05** — full CSP/web-hardening review.
- ⬜ **US-P0-07** — freshness suppression coverage audit.

## Backlog / other candidate tracks
- ⬜ Browser phase (`DOCS/handoff/CLAUDE_CODE_HANDOFF_DESK_W1.md`): e2e matrix, screenshots, gates G-1..G-7, then flip `FEATURE_DESK_V2`.
- ⬜ Operator items: E1 (rotate PAT — treat as compromised), E7 (torch worker), E8 (Finnhub social tier).

## Carried caveat
- 🟡 `research/finrlx_cpu/*.json` registries are dirty from a local test run (UUID/timestamp churn) — deliberately **not committed**. Restore or ignore at will.

---
_This table is the live view. `SESSION_STATE.md` holds the narrative resume detail._
