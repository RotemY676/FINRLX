# Phase 20 — Universe CRUD

**Source:** Phase 19 audit follow-up. The Universe page on production has been a read-only viewer over a single seeded universe; `manage-your-universe.md` documented an Add/Remove workflow that was never implemented. This phase closes the gap.

**Total estimate:** ~2 working days, spread over 6 commits with live-verify between each.

---

## Scope

In:
- Create, rename, soft-deactivate universes
- Add asset to universe (by ticker)
- Remove asset from universe (soft, preserves history)
- Asset autocomplete endpoint (already-present tickers from `assets` table)
- Frontend toolbar + dialogs on `/universe`
- Refresh `manage-your-universe.md` to match what ships

Out of scope (deliberate):
- Multi-user collaboration on a universe (added_by / locking) — defer
- Effective-date scheduling ("add this on T+1") — defer; everything is immediate
- Hard delete of universes referenced by historical recommendations / backtests — those universes go `is_active=false`, never DELETE
- Ticker creation from scratch — assets table is seeded by ingestion, we only let users pick existing ones

---

## Data model changes

| Table | Column | Why |
|---|---|---|
| `universe_memberships` | new column `removed_at: DateTime | None` | Soft-delete preserves audit history (`added_at`–`removed_at` defines the membership window) without breaking the (universe_id, asset_id) composite PK. Re-adding the same asset clears `removed_at`. |
| `universes` | (no change) | Existing `is_active` flag handles "deactivated" universes. |

Single Alembic migration. No data backfill needed (existing rows have `removed_at = NULL` = "currently a member" which is correct).

---

## Sequencing

| Sub-phase | Files | Acceptance |
|---|---|---|
| **20.0** Plan + issue | this file, `gh issue create` | Issue open with the acceptance criteria below |
| **20.1** Backend Universe CRUD | `app/services/universe.py`, `app/api/v1/universe.py`, `app/schemas/universe.py` (new), tests | POST/PATCH/DELETE on `/universes`; rename / deactivate works; can't deactivate the only universe; tests pass |
| **20.2** Backend membership CRUD + migration | + Alembic migration, more service + endpoint methods | POST `/universes/{id}/assets`, DELETE `/universes/{id}/assets/{asset_id}`; soft-delete via `removed_at`; re-add clears it; tests pass |
| **20.3** Asset autocomplete | `app/api/v1/assets.py` (new) | GET `/assets?q=AAP` returns ranked match list; tests pass |
| **20.4** Frontend Universe CRUD UI | `frontend/src/app/universe/page.tsx`, `services/api.ts`, new components | "New", "Rename", "Deactivate" buttons wired to real endpoints; vitest passes |
| **20.5** Frontend membership UI | `frontend/src/components/universe/AssetPicker.tsx` (new), wire into page | Add-asset modal with autocomplete; remove confirmation; vitest passes |
| **20.6** Help doc refresh | `frontend/src/content/help/guides/manage-your-universe.md` | Doc matches what now actually ships; no false promises |

Each sub-phase: typecheck + tests pass → commit → push → wait for Railway → verify on production → next.

---

## Tests per sub-phase (target)

- 20.1: ~6 tests — create / duplicate-name / rename / deactivate-only-one / rename-not-found / list-includes-inactive=false
- 20.2: ~7 tests — add / add-duplicate-active / add-readds-after-remove / remove / remove-already-removed / remove-bad-asset / migration columns present
- 20.3: ~4 tests — prefix match / case-insensitive / empty-q returns top-N / limit applied
- 20.4 / 20.5: vitest for the new components; production smoke after deploy
- 20.6: vitest for any new MDX link target; live verify the page renders

---

## Risk + rollback

- 20.2 migration is additive (`ADD COLUMN removed_at`) so Alembic downgrade is trivial (`DROP COLUMN`).
- Soft-delete avoids losing data. Worst-case recovery: clear all `removed_at` on the affected universe to restore membership.
- The frontend additions are net-new components; no existing surface is being repurposed, so a partial Phase 20 rollback removes only the new toolbar/dialogs without touching the read-only viewer paths from Phase 6F.

---

## Out-of-scope acknowledgements (for the future-work doc)

- Concurrent edit safety. Two operators adding the same asset at the same time would race. Acceptable in the MVP — there's only one operator today. Add ETags / optimistic concurrency in Phase 21+ if needed.
- Bulk import (paste a list of tickers). The audit said add-one-at-a-time is enough; defer bulk to a clear product need.
