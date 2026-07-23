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

from app.core.route_policy import AUTH_DEBT_BASELINE

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
]

GATED_GROUPS = (
    "models", "paper", "ops", "universes",
    "policies", "backtests", "integrations", "publication",
    "ml-ops", "actions", "research", "replay", "risk",
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


def test_frontend_anonymous_surfaces_are_still_recorded_as_debt():
    """These must not be gated until the client sends a bearer.

    The beta auth model says "the FE sends a bearer on every call", but that is
    not yet true for these routes — the Simple Mode front door and the desk
    fetch them with no Authorization header. Gating them would take the public
    product down, so they remain recorded debt rather than being quietly
    gated or quietly moved to the public allowlist. This test fails if someone
    gates them without doing the client work first.
    """
    missing = [p for p in FE_ANONYMOUS_TODAY
               if not any(p in e for e in AUTH_DEBT_BASELINE)]
    assert missing == [], (
        "these are called anonymously by the frontend but are no longer "
        f"recorded as debt — gating them breaks the live product: {missing}"
    )
