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

## Track P0 — Security/Ops hardening (inherited, in flight)

| # | Task | Owner | Gate | Status | Notes |
|---|---|---|---|---|---|
| P0-01 | Runtime inventory manifest (admin-only) | — | — | ✅ | On `main` (commit cff56c5). |
| P0-03 | Route authorization matrix + gov-mutation auth | — | — | ✅ | On `main` (a8633f3, 20483af). |
| P0-08 | Unified readiness endpoint + jobs component | — | — | ✅ | On `main` (e3ba39a, d1a772d). |
| P0-?? | Ingest authz (`test_p0_ingest_authz.py` + edits) | — | — | 🟡 | **Uncommitted in working tree.** Predates governance; review & commit separately with user. |

## Backlog / candidate next tracks
- ⬜ Browser phase (`DOCS/handoff/CLAUDE_CODE_HANDOFF_DESK_W1.md`): e2e matrix, screenshots, gates G-1..G-7, then flip `FEATURE_DESK_V2`.
- ⬜ Operator items: E1 (rotate PAT — treat as compromised), E7 (torch worker), E8 (Finnhub social tier).

---
_This table is the live view. `SESSION_STATE.md` holds the narrative resume detail._
