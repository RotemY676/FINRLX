"""Route authorization policy + audit (US-P0-03).

This module makes the authorization posture of every HTTP route *explicit* and
enforceable. It splits the currently-unauthenticated ("public") routes into two
sets:

* ``PUBLIC_ALLOWLIST`` — endpoints that are **intentionally** unauthenticated
  (health probes, feature flags for the FE boot, the auth entry points). Adding
  a route here is a deliberate, reviewed decision.

* ``AUTH_DEBT_BASELINE`` — endpoints that are unauthenticated **today but should
  not be**. This is recorded, labeled P0 security debt captured on 2026-07-21.
  The audit test enforces a one-way ratchet: this set may only *shrink* (as
  routes get auth-gated) and no *new* unauthenticated route may appear outside
  these two sets. This neither hides the gap (it is fully enumerated and
  surfaced in the runtime-inventory manifest) nor rubber-stamps it as safe.

Entries are keyed as ``"METHOD /path"``. The audit is pure and dependency-free
so it can run in unit tests and feed the operator manifest.
"""
from __future__ import annotations

from collections.abc import Iterable

# Intentionally unauthenticated — reviewed and accepted as public.
PUBLIC_ALLOWLIST: frozenset[str] = frozenset(
    {
        "GET /",
        "GET /health",
        "GET /healthz",
        "GET /api/health",
        "GET /api/v1/health",
        "GET /api/v1/flags",
        "POST /api/v1/auth/login",
        "POST /api/v1/auth/signup",
        "POST /api/v1/auth/refresh",
        "GET /api/v1/auth/google/start",
        "GET /api/v1/auth/google/callback",
    }
)

# KNOWN P0 SECURITY DEBT (captured 2026-07-21): unauthenticated today, should be
# gated. This set may only shrink. Do NOT add entries to make a new route pass —
# a new unauthenticated route must either be justified in PUBLIC_ALLOWLIST or
# given an auth dependency.
AUTH_DEBT_BASELINE: frozenset[str] = frozenset(
    {
        "DELETE /api/v1/universes/{universe_id}",
        "DELETE /api/v1/universes/{universe_id}/assets/{asset_id}",
        "GET /api/v1/activity",
        "GET /api/v1/analysis/single-ticker",
        "GET /api/v1/assets",
        "GET /api/v1/autopilot/compare",
        "GET /api/v1/autopilot/desk/{ticker}/status",
        "GET /api/v1/autopilot/desk/{ticker}/{section}",
        "GET /api/v1/autopilot/dossier",
        "GET /api/v1/backtests",
        "GET /api/v1/backtests/status",
        "GET /api/v1/backtests/{backtest_id}",
        "GET /api/v1/backtests/{backtest_id}/decisions",
        "GET /api/v1/backtests/{backtest_id}/equity-curve",
        "GET /api/v1/comparison/current",
        "GET /api/v1/engines/comparison",
        "GET /api/v1/engines/definitions",
        "GET /api/v1/engines/disagreement",
        "GET /api/v1/engines/evidence",
        "GET /api/v1/engines/latest-signals",
        "GET /api/v1/engines/runs",
        "GET /api/v1/engines/runs/{run_id}",
        "GET /api/v1/engines/status",
        "GET /api/v1/features/definitions",
        "GET /api/v1/features/latest",
        "GET /api/v1/features/status",
        "GET /api/v1/features/{feature_set_id}",
        "GET /api/v1/ingest/manifests",
        "GET /api/v1/ingest/status",
        "GET /api/v1/integrations",
        "GET /api/v1/integrations/health",
        "GET /api/v1/integrations/readiness",
        "GET /api/v1/integrations/{source_key}",
        "GET /api/v1/ml-ops/models/{model_key}",
        "GET /api/v1/ml-ops/models/{model_key}/shadow-status",
        "GET /api/v1/ml-ops/models/{model_key}/warnings",
        "GET /api/v1/ml-ops/summary",
        "GET /api/v1/models/definitions",
        "GET /api/v1/models/predictions",
        "GET /api/v1/models/promotion/history",
        "GET /api/v1/models/promotion/latest",
        "GET /api/v1/models/promotion/{review_id}",
        "GET /api/v1/models/runs",
        "GET /api/v1/models/status",
        "GET /api/v1/models/validation/history",
        "GET /api/v1/models/validation/latest",
        "GET /api/v1/models/validation/{report_id}",
        "GET /api/v1/news",
        "GET /api/v1/ops",
        "GET /api/v1/ops/audit",
        "GET /api/v1/ops/breaches",
        "GET /api/v1/ops/data-health",
        "GET /api/v1/ops/engines",
        "GET /api/v1/ops/feeds",
        "GET /api/v1/ops/incidents",
        "GET /api/v1/ops/queue",
        "GET /api/v1/overview",
        "GET /api/v1/paper",
        "GET /api/v1/paper/current",
        "GET /api/v1/paper/current/valuation-in-currency",
        "GET /api/v1/paper/{portfolio_id}",
        "GET /api/v1/paper/{portfolio_id}/attribution/assets",
        "GET /api/v1/paper/{portfolio_id}/attribution/decisions",
        "GET /api/v1/paper/{portfolio_id}/drift",
        "GET /api/v1/paper/{portfolio_id}/events",
        "GET /api/v1/paper/{portfolio_id}/performance",
        "GET /api/v1/paper/{portfolio_id}/trades",
        "GET /api/v1/paper/{portfolio_id}/valuations",
        "GET /api/v1/pipeline/latest",
        "GET /api/v1/pipeline/runs",
        "GET /api/v1/pipeline/runs/{recommendation_id}",
        "GET /api/v1/pipeline/status",
        "GET /api/v1/policies/breaches",
        "GET /api/v1/policies/rules",
        "GET /api/v1/policies/rules/{key}",
        "GET /api/v1/policies/rules/{key}/history",
        "GET /api/v1/pricechart",
        "GET /api/v1/prices/freshness",
        "GET /api/v1/publication/queue",
        "GET /api/v1/publication/recommendations/{rec_id}/gates",
        "GET /api/v1/publication/recommendations/{rec_id}/history",
        "GET /api/v1/publication/status",
        "GET /api/v1/recommendations/current",
        "GET /api/v1/recommendations/{recommendation_id}",
        "GET /api/v1/recommendations/{recommendation_id}/stages",
        "GET /api/v1/regime",
        "GET /api/v1/replay",
        "GET /api/v1/replay/{recommendation_id}",
        "GET /api/v1/research/fundamentals/_status",
        "GET /api/v1/research/fundamentals/{ticker}",
        "GET /api/v1/research/peers/{ticker}",
        "GET /api/v1/risk/current",
        "GET /api/v1/risk/portfolios/{portfolio_id}",
        "GET /api/v1/rl/adapter/status",
        "GET /api/v1/rl/agents",
        "GET /api/v1/rl/agents/{agent_key}",
        "GET /api/v1/rl/benchmarks",
        "GET /api/v1/rl/benchmarks/audit",
        "GET /api/v1/rl/benchmarks/{benchmark_report_id}",
        "GET /api/v1/rl/benchmarks/{benchmark_report_id}/audit",
        "GET /api/v1/rl/dataset/export",
        "GET /api/v1/rl/environments",
        "GET /api/v1/rl/environments/{key}",
        "GET /api/v1/rl/episodes/{episode_id}/steps",
        "GET /api/v1/rl/finrlx/candidates",
        "GET /api/v1/rl/finrlx/candidates/{candidate_id}",
        "GET /api/v1/rl/finrlx/candidates/{candidate_id}/benchmark-eligibility",
        "GET /api/v1/rl/finrlx/candidates/{candidate_id}/benchmarks",
        "GET /api/v1/rl/finrlx/candidates/{candidate_id}/isolation",
        "GET /api/v1/rl/finrlx/dataset-exports",
        "GET /api/v1/rl/finrlx/dataset-exports/{export_id}",
        "GET /api/v1/rl/finrlx/dataset-exports/{export_id}/verify",
        "GET /api/v1/rl/finrlx/dependencies",
        "GET /api/v1/rl/finrlx/experiment-comparisons",
        "GET /api/v1/rl/finrlx/experiment-comparisons/{comparison_id}",
        "GET /api/v1/rl/finrlx/experiment-comparisons/{comparison_id}/verify",
        "GET /api/v1/rl/finrlx/persistence/status",
        "GET /api/v1/rl/finrlx/registry-metadata/status",
        "GET /api/v1/rl/finrlx/research-experiments",
        "GET /api/v1/rl/finrlx/research-experiments/{experiment_id}",
        "GET /api/v1/rl/finrlx/research-experiments/{experiment_id}/verify",
        "GET /api/v1/rl/finrlx/research-readiness",
        "GET /api/v1/rl/finrlx/research-readiness/{readiness_id}",
        "GET /api/v1/rl/finrlx/research-readiness/{readiness_id}/verify",
        "GET /api/v1/rl/finrlx/status",
        "GET /api/v1/rl/policies",
        "GET /api/v1/rl/policies/{policy_snapshot_id}",
        "GET /api/v1/rl/runs",
        "GET /api/v1/rl/runs/{run_id}",
        "GET /api/v1/rl/runs/{run_id}/episodes",
        "GET /api/v1/rl/status",
        "GET /api/v1/rl/training-runs",
        "GET /api/v1/rl/training-runs/{run_id}",
        "GET /api/v1/scenario/baseline",
        "GET /api/v1/universes",
        "GET /api/v1/universes/default",
        "GET /api/v1/universes/{universe_id}",
        "GET /api/v1/universes/{universe_id}/coverage",
        "GET /api/v1/universes/{universe_id}/readiness",
        "GET /api/v1/workspace-counts",
        "PATCH /api/v1/policies/rules/{key}",
        "PATCH /api/v1/universes/{universe_id}",
        "POST /api/v1/actions/defer",
        "POST /api/v1/actions/promote-paper",
        "POST /api/v1/actions/save-thesis",
        "POST /api/v1/backtests/run",
        "POST /api/v1/engines/run",
        "POST /api/v1/features/compute",
        # NOTE: POST /ingest/bars and /ingest/news were auth-gated on 2026-07-21
        # (US-P0-03 enforcement, increment 2) — controlling market-data injection
        # is a zero-fiction control. Removed from the baseline (now require auth).
        "POST /api/v1/models/predict",
        "POST /api/v1/models/promotion/review",
        "POST /api/v1/models/promotion/{review_id}/decision",
        "POST /api/v1/models/train",
        "POST /api/v1/models/validation/run",
        "POST /api/v1/ops/incidents/{incident_id}/resolve",
        "POST /api/v1/ops/queue/{item_id}/approve",
        "POST /api/v1/ops/queue/{item_id}/challenge",
        "POST /api/v1/ops/queue/{item_id}/defer",
        "POST /api/v1/paper/from-recommendation/{recommendation_id}",
        "POST /api/v1/paper/{portfolio_id}/performance/recompute",
        "POST /api/v1/paper/{portfolio_id}/rebalance/{recommendation_id}",
        "POST /api/v1/pipeline/run",
        "POST /api/v1/policies/evaluate",
        # NOTE: the 5 publication governance mutations (stage/approve/publish/
        # defer/suppress) were auth-gated on 2026-07-21 (US-P0-03 enforcement,
        # slice 1) and intentionally removed from this baseline — they now
        # require authentication and are no longer public debt.
        "POST /api/v1/rl/benchmarks/compare-policy",
        "POST /api/v1/rl/benchmarks/run",
        "POST /api/v1/rl/environments/{key}/validate",
        "POST /api/v1/rl/finrlx/candidates/{candidate_id}/benchmark",
        "POST /api/v1/rl/finrlx/dataset-export",
        "POST /api/v1/rl/finrlx/dataset-exports/rebuild-registry",
        "POST /api/v1/rl/finrlx/dataset-exports/{export_id}/mark-stale",
        "POST /api/v1/rl/finrlx/experiment-comparisons",
        "POST /api/v1/rl/finrlx/experiment-comparisons/rebuild-registry",
        "POST /api/v1/rl/finrlx/experiment-comparisons/{comparison_id}/archive",
        "POST /api/v1/rl/finrlx/import-research-artifact",
        "POST /api/v1/rl/finrlx/registry-metadata/sync",
        "POST /api/v1/rl/finrlx/research-experiments",
        "POST /api/v1/rl/finrlx/research-experiments/rebuild-registry",
        "POST /api/v1/rl/finrlx/research-experiments/{experiment_id}/results",
        "POST /api/v1/rl/finrlx/research-experiments/{experiment_id}/state",
        "POST /api/v1/rl/finrlx/research-readiness",
        "POST /api/v1/rl/finrlx/research-readiness/rebuild-registry",
        "POST /api/v1/rl/finrlx/research-readiness/{readiness_id}/archive",
        "POST /api/v1/rl/finrlx/research-readiness/{readiness_id}/state",
        "POST /api/v1/rl/finrlx/train-cpu-prototype",
        "POST /api/v1/rl/finrlx/train-research",
        "POST /api/v1/rl/finrlx/validate-dataset",
        "POST /api/v1/rl/finrlx/validate-research-artifact",
        "POST /api/v1/rl/policies/{policy_snapshot_id}/evaluate",
        "POST /api/v1/rl/simulations/run",
        "POST /api/v1/rl/train",
        "POST /api/v1/scenario/simulate",
        "POST /api/v1/universes",
        "POST /api/v1/universes/{universe_id}/assets",
    }
)


def classify_public_routes(public_entries: Iterable[str]) -> dict[str, list[str]]:
    """Split currently-public routes into allowed / known-debt / unclassified.

    ``unclassified`` is the enforcement signal: it must always be empty. A
    non-empty result means a route is unauthenticated without being either an
    accepted public endpoint or previously-recorded debt — i.e. a new exposure
    that must be triaged before merge.
    """
    entries = set(public_entries)
    return {
        "allowed": sorted(entries & PUBLIC_ALLOWLIST),
        "debt": sorted(entries & AUTH_DEBT_BASELINE),
        "unclassified": sorted(entries - PUBLIC_ALLOWLIST - AUTH_DEBT_BASELINE),
    }
