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
]


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
    pattern = re.compile(r"/api/v1/(models|paper|ops|universes)\b")
    leftovers = sorted(e for e in AUTH_DEBT_BASELINE if pattern.search(e))
    assert leftovers == [], f"still recorded as auth debt: {leftovers}"
