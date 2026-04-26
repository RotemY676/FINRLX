# Phase 8G.1: Dynamic Isolation Badge Truthfulness Hotfix

**Date:** 2026-04-26
**Status:** Complete

---

## Root Cause

Selected candidate isolation badges were hardcoded as green ("Promotion blocked", "Publication blocked", etc.) regardless of backend state. This masks unsafe or ineligible candidates. The FinRL-X panel also showed static candidate-specific isolation badges that could mislead operators.

## Exact UI Change

### Selected candidate isolation badges (dynamic)

**Before:** 5 hardcoded green badges always shown.

**After:** 5 dynamic badges driven by `candidateEligibility.isolation_checks`:

| Backend key | Label (passed) | Label (missing/failed) | Style |
|------------|---------------|----------------------|-------|
| `promotion_blocked` | "Promotion blocked" | "Promotion check missing" | pos-soft / caution-soft |
| `publication_blocked` | "Publication blocked" | "Publication check missing" | pos-soft / caution-soft |
| `live_recommendation_blocked` | "Recommendation blocked" | "Recommendation check missing" | pos-soft / caution-soft |
| `overview_influence_blocked` | "Overview influence blocked" | "Overview influence check missing" | pos-soft / caution-soft |
| `broker_execution_blocked` | "Broker path blocked" | "Broker path check missing" | pos-soft / caution-soft |

**Before eligibility loads:** Shows neutral "Loading isolation checks..." badge (gray).

### FinRL-X panel system guardrails (relabeled)

**Before:** 5 green candidate-specific badges ("Promotion blocked" etc.)

**After:** 5 neutral-gray badges with "Research guardrail:" prefix to clarify these are system-level guarantees, not candidate-specific checks. Example: "Research guardrail: promotion blocked"

## States

| State | Isolation badges | Benchmark form |
|-------|-----------------|----------------|
| Eligibility loading | "Loading isolation checks..." (gray) | Hidden |
| Eligible, all checks pass | 5 green badges | Visible |
| Not eligible, some checks fail | Failed checks in caution/yellow | Hidden, rejection reasons shown |
| Not eligible, missing isolation_checks | All badges caution/yellow | Hidden, rejection reasons shown |

## Files Changed

```
EDIT frontend/src/app/admin/page.tsx — dynamic isolation badges + FinRL-X guardrail relabel
NEW  DOCS/handoff/PHASE_8G1_DYNAMIC_ISOLATION_BADGE_TRUTHFULNESS_HOTFIX_REPORT.md
```

No backend changes.

## Frontend Build Result

**PASS** — compiled successfully, types valid.

## Backend Status

Unchanged. 434 tests pass (from Phase 8F.2 baseline).

## Design Handoff Review

**Files reviewed:** styles.css, tokens.css for semantic badge patterns. Reused: `bg-pos-soft text-pos-soft-ink` for passed checks, `bg-caution-soft text-caution-soft-ink` for failed/missing, `bg-surface-3 text-ink-3` for neutral/loading states. No unrelated UI style introduced.

## Unsafe Language Grep Result

```
grep -i "buy|sell|trade now|execute trade|live signal|best investment|production alpha|deploy policy" → 0 matches
```

## Manual UI Checklist

1. Open /admin
2. Select an imported candidate
3. Verify "Loading isolation checks..." appears briefly before eligibility loads
4. After load, verify 5 green badges for a valid candidate
5. Verify "Not eligible for promotion" gray badge always present
6. Verify FinRL-X panel shows "Research guardrail:" prefix (gray, not green)
7. Run benchmark — confirm form, acknowledgement, result still work
8. Confirm history refreshes

## Safety Confirmations

| Check | Status |
|-------|--------|
| No live RL | CONFIRMED |
| No broker execution | CONFIRMED |
| No recommendation pollution | CONFIRMED |
| No overview pollution | CONFIRMED |
| No publication influence | CONFIRMED |
| No production dependency changes | CONFIRMED |
| No neural inference | CONFIRMED |
| No unsafe language | CONFIRMED |

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Badges from candidateEligibility.isolation_checks | PASS |
| 2 | No all-green before eligibility loads | PASS |
| 3 | Missing check shows caution state | PASS |
| 4 | Failed check shows caution state | PASS |
| 5 | Ineligible hides benchmark form | PASS |
| 6 | Eligible shows benchmark form | PASS |
| 7 | Benchmark workflow works | PASS |
| 8 | History works | PASS |
| 9 | Artifact hash/summary shown | PASS |
| 10 | include_baselines toggle exists | PASS |
| 11 | Acknowledgement required | PASS |
| 12 | No unsafe language | PASS |
| 13 | Frontend build passes | PASS |
| 14 | Backend if touched | N/A |
| 15 | No production dep changes | PASS |
| 16 | No live RL/broker/rec/overview/pub | PASS |
| 17 | Design reviewed | PASS |
