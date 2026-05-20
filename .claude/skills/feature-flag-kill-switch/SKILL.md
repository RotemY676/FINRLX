---
name: feature-flag-kill-switch
description: Wrap every user-facing surface (research-lane, paper-trading, backtests, replay) behind a feature flag that can be flipped via env var without redeploy. Use when adding any new surface area, when an outage requires emergency hiding of a feature, or when scoping what beta testers see.
source: project
---

# FINRLX — Feature-Flag Kill-Switch

## Use this skill when

- Adding a new top-level navigation entry or page
- Adding a new admin/research/experimental surface
- An outage requires hiding a feature without redeploy
- Scoping which surfaces beta testers see
- Reviewing the sidebar / TopBar / route layout

## Do not use this skill when

- You are only changing styling or internal component code
- The change is inside a surface that is already gated

## Iron rule

Every user-facing surface must have a kill switch reachable from a single env var. The frontend reads `/api/v1/flags` once at boot, exposes it via `FeatureFlagsContext`, and any navigation entry that exposes a gated surface must be conditional on the corresponding flag.

## How to apply

### Backend
- Each flag is declared in `backend/app/core/config.py` as `feature_<name>: bool = True` (default ON so test envs stay green).
- The `/api/v1/flags` endpoint in `backend/app/api/v1/flags.py` returns the dict the frontend reads.
- Production overrides via env vars: `FEATURE_RESEARCH_LANE=false`, etc.
- Backend routes are NOT hard-gated by default — testers can't navigate there if the UI doesn't expose them, which is sufficient for closed beta. Add a `requires_feature(flag)` Depends() ONLY if there's a security requirement to harden against direct API calls.

### Frontend
- A `FeatureFlagsContext` (in `frontend/src/contexts/`) fetches `/api/v1/flags` at mount and exposes a `useFeatureFlags()` hook.
- Any `<Sidebar />` or `<TopBar />` entry that links into a gated surface MUST be wrapped: `{flags.research_lane && <ResearchNavGroup />}`.
- Defaults during the loading state: assume the flag is OFF (fail-closed). This prevents flash-of-restricted-content.

### Adding a new flag
1. Add `feature_<name>: bool = True` to `Settings` in `backend/app/core/config.py`.
2. Add a key in `backend/app/api/v1/flags.py`'s response payload.
3. Add the field to `FeatureFlags` type in `frontend/src/contexts/FeatureFlagsContext.tsx`.
4. Wrap the affected nav entries with `{flags.<name> && ...}`.

### Removing a flag
1. Delete the navigation conditional (always show or always hide).
2. Delete the flag from the backend `Settings` and the `/flags` payload.
3. Delete the field from the frontend type.
4. Search for stale `flags.<name>` references.

## Why

- Closed-beta operators must be able to flip a single env var to hide a half-baked surface without redeploying.
- A flag-off-by-default policy lets us land code on `main` ahead of a feature being user-ready.
- During an incident, hiding a surface from users is faster than reverting code.

## Pitfalls

- Forgetting `loading=true → flags fail-closed` causes flashes of restricted content during boot.
- Defaulting to OFF in tests breaks the existing test suite. Backend defaults are ON; production overrides to OFF.
- Hard-gating backend routes by flag breaks all the existing tests at once. Don't do that without paving the way with a transition.
- A flag should be either temporary (one-week launch shield) OR a permanent kill switch — never "we'll decide later". Document which.
