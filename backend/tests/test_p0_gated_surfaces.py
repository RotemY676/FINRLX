"""US-P0-03 batch 2 — models / paper / ops / universes refuse anonymous callers.

51 more of the audited debt routes: model training and promotion decisions,
paper-portfolio mutations, the operator queue and incident resolution, and
universe CRUD. All of them mutate state or expose operator surfaces.

As with batch 1, this asserts *runtime* behaviour. `test_p0_route_authz.py`
ratchets the declared policy, but a shrinking baseline proves nothing on its
own — entries could be deleted with nothing actually gated. Each route is
checked twice: it must refuse anonymously, and it must not refuse a genuine
operator bearer (otherwise "gated" would just mean "broken").
"""
from __future__ import annotations

import re

import pytest

from app.core.route_policy import AUTH_DEBT_BASELINE, PUBLIC_ALLOWLIST

GATED = [
    # models — training, prediction, validation, promotion decisions
    ("get", "/api/v1/models/definitions"),
    ("get", "/api/v1/models/status"),
    ("get", "/api/v1/models/validation/latest"),
    ("get", "/api/v1/models/promotion/latest"),
    ("post", "/api/v1/models/train"),
    # paper — portfolio state and mutations
    ("get", "/api/v1/paper"),
    ("get", "/api/v1/paper/current"),
    # ops — operator queue, incidents, feeds
    ("get", "/api/v1/ops/queue"),
    ("get", "/api/v1/ops/incidents"),
    ("get", "/api/v1/ops/feeds"),
    ("get", "/api/v1/ops/data-health"),
    # universes — CRUD over the investable set
    ("get", "/api/v1/universes"),
    ("get", "/api/v1/universes/default"),
    ("post", "/api/v1/universes"),
    # ── batch 3: operator / research surfaces ──
    ("get", "/api/v1/policies/rules"),
    ("get", "/api/v1/policies/breaches"),
    ("get", "/api/v1/backtests"),
    ("get", "/api/v1/backtests/status"),
    ("get", "/api/v1/integrations"),
    ("get", "/api/v1/integrations/health"),
    ("get", "/api/v1/publication/queue"),
    ("get", "/api/v1/publication/status"),
    ("get", "/api/v1/ml-ops/summary"),
    ("get", "/api/v1/replay"),
    ("get", "/api/v1/risk/current"),
    ("get", "/api/v1/research/fundamentals/_status"),
    ("post", "/api/v1/actions/defer"),
    ("post", "/api/v1/backtests/run"),
    # ── batch 4: compute surfaces ──
    ("get", "/api/v1/engines/status"),
    ("get", "/api/v1/engines/definitions"),
    ("get", "/api/v1/features/status"),
    ("get", "/api/v1/features/latest"),
    ("get", "/api/v1/pipeline/status"),
    ("get", "/api/v1/pipeline/runs"),
    ("post", "/api/v1/engines/run"),
    ("post", "/api/v1/features/compute"),
    ("post", "/api/v1/pipeline/run"),
]

GATED_GROUPS = (
    "models", "paper", "ops", "universes",
    "policies", "backtests", "integrations", "publication",
    "ml-ops", "actions", "research", "replay", "risk",
    "engines", "features", "pipeline", "scenario", "ingest",
)

# Surfaces the frontend still calls WITHOUT a bearer today. Gating these would
# take the public product down, so they stay as recorded debt until the client
# sends credentials. Named here so the gap is explicit rather than forgotten.
FE_ANONYMOUS_TODAY = (
    "/api/v1/autopilot/dossier",
    "/api/v1/autopilot/compare",
    "/api/v1/autopilot/desk/{ticker}/status",
    "/api/v1/autopilot/desk/{ticker}/{section}",
    "/api/v1/assets",
    "/api/v1/prices/freshness",
)


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path", GATED)
async def test_rejects_anonymous(anon_client, method, path):
    res = await getattr(anon_client, method)(path)
    assert res.status_code == 401, (
        f"{method.upper()} {path} answered {res.status_code} without credentials"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path", GATED)
async def test_accepts_an_operator_bearer(client, method, path):
    """Gated must not mean broken — a real bearer still reaches the handler."""
    res = await getattr(client, method)(path)
    assert res.status_code != 401, f"{method.upper()} {path} rejected a valid bearer"


def test_gated_groups_are_out_of_the_debt_baseline():
    pattern = re.compile(r"/api/v1/(" + "|".join(GATED_GROUPS) + r")\b")
    leftovers = sorted(e for e in AUTH_DEBT_BASELINE if pattern.search(e))
    assert leftovers == [], f"still recorded as auth debt: {leftovers}"


def test_no_remaining_debt_route_mutates_state():
    """The invariant the bulk gating bought.

    Whatever is still unauthenticated must be read-only. Every mutating route
    — anything that trains a model, moves a portfolio, resolves an incident,
    edits a universe or ingests market data — is now gated. If a POST / PUT /
    PATCH / DELETE ever reappears in the baseline, an unauthenticated caller
    can change server state and this fails.
    """
    mutating = sorted(
        e for e in AUTH_DEBT_BASELINE
        if e.split(" ", 1)[0] in {"POST", "PUT", "PATCH", "DELETE"}
    )
    assert mutating == [], (
        "unauthenticated routes that can change state: " + ", ".join(mutating)
    )


def test_the_anonymous_research_product_is_explicitly_allowlisted():
    """The six public routes are a reviewed decision, not leftover debt.

    Product decision 2026-07-23: a logged-out visitor can research any ticker.
    These six carry that flow. They must sit in PUBLIC_ALLOWLIST — where the
    rationale is written down and adding to it is a deliberate act — and not
    drift back into the debt set, which would misreport a decision as a defect.
    """
    for path in FE_ANONYMOUS_TODAY:
        assert any(path in e for e in PUBLIC_ALLOWLIST), (
            f"{path} carries the anonymous research flow but is not in "
            "PUBLIC_ALLOWLIST — gating it breaks the live product"
        )
        assert not any(path in e for e in AUTH_DEBT_BASELINE), (
            f"{path} is an accepted public route; it should not also be "
            "recorded as debt"
        )


def test_the_auth_debt_is_cleared():
    """US-P0-03 exit condition.

    192 routes were recorded as debt on 2026-07-21. This asserts the set is now
    empty — 186 gated, 6 reviewed and moved to the allowlist. With the baseline
    empty the ratchet bites harder than before: any new unauthenticated route is
    unclassified and fails the audit outright.
    """
    assert sorted(AUTH_DEBT_BASELINE) == [], (
        "auth debt is not empty: " + ", ".join(sorted(AUTH_DEBT_BASELINE))
    )
