# Phase 19F — authenticated sweep runbook

**Purpose:** Re-run the production a11y / console sweep with a real session so the auth-gated routes (decision detail, paper portfolio, replay, ops drill-down) are exercised in their post-fetch state, not just their login-wall fallback.

**Status:** Framework shipped (spec at `frontend/tests/e2e/_site-sweep-auth.spec.ts`). Not yet executed — requires operator-provisioned credentials.

---

## Why we shipped this as a template (not a one-shot run)

The unauthenticated sweep (Phase 18J + 19A–E verifications) covers what a logged-out visitor sees. The authenticated routes render a login wall in that mode, so the sweep can't reach the data-bearing UI states.

Running the auth sweep needs credentials on production. We deliberately do not check in a test account — partly to avoid creating a stale shared account, partly so the operator who runs the sweep has to make a deliberate decision to authenticate against production. The spec is gated on a four-env-var contract so it stays a no-op until you explicitly opt in.

## How to run it

```bash
# 1. Provision a sandboxed user on production (one-time).
#    Recommend: qa+sweep@finrlx.local with a 16-char random password.
#    Complete onboarding so the wizard doesn't intercept the sweep.

# 2. Run the spec from frontend/:
cd frontend
SWEEP_AUTH=1 \
PLAYWRIGHT_BASE_URL=https://frontend-production-7e8b1.up.railway.app \
PLAYWRIGHT_DISABLE_WEBSERVER=1 \
SWEEP_AUTH_EMAIL=qa+sweep@finrlx.local \
SWEEP_AUTH_PASSWORD=<from-vault> \
  npx playwright test tests/e2e/_site-sweep-auth.spec.ts --workers=4

# 3. Outputs land under
#    DOCS/handoff/_phase19f_auth_sweep_YYYY-MM-DD/
#      - findings/<viewport>__<route>.json    (axe + console per route×viewport)
#      - screenshots/<viewport>/<route>.png   (full-page)
```

## How to read the output

Use the existing `aggregate.py` pattern from `_phase18sweep_2026-05-23/` — copy it into the new dated dir and `python aggregate.py`. The aggregator produces a per-route axe rollup plus per-viewport screenshot index.

## What counts as a regression

After Phase 19A–E:
- `KNOWN_PREEXISTING_RULES` contains exactly **`svg-img-alt`** (Recharts limitation, issue #7).
- Any *other* serious-or-critical rule found by the auth sweep is a new regression and should block the next release.

To tighten further once Recharts is upgraded or worked around:
1. Remove `svg-img-alt` from `KNOWN_PREEXISTING_RULES` in `tests/e2e/_helpers/axe.ts`.
2. Re-run the auth sweep. Any svg-img-alt firing now fails the gate.

## Security note

The login form on production accepts plain credentials. The spec stores the resulting session in `.playwright-state/auth-sweep-<pid>.json` and reuses it across tests in one run. The state file is per-PID and ephemeral — sweep run, state created, run ends, file orphaned. The directory is `.gitignore`'d via the existing `.playwright-state/*` pattern; verify it stays out of git before the first run.

Do NOT bake credentials into CI without first scoping the test user to a dedicated tenant and policy that cannot mutate other users' data.

## Operator checklist

- [ ] Test user provisioned on prod (or staging if available)
- [ ] Credentials stored in your secrets manager (NOT in .env files in repo)
- [ ] First sweep run produces a fresh `_phase19f_auth_sweep_<date>/` dir
- [ ] Per-route axe rollup shows 0 critical + 0 serious (excluding the known `svg-img-alt`)
- [ ] If anything else fires: open an issue, do NOT silence it in `KNOWN_PREEXISTING_RULES` without a real fix
