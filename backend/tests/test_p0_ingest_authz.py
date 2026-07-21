"""US-P0-03 enforcement — market-data ingestion mutations require auth.

Injecting bars/news is a zero-fiction control surface: an anonymous caller must
never be able to write market data. The 401 checks are side-effect-free (auth is
enforced before the handler body runs, so no manifest is written). The authed
ingestion path itself is exercised end-to-end by test_phase4a_ingestion.py under
its operator-override fixture, so no polluting positive call is repeated here.
"""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(("kind", "body"), [("bars", {"source": "local"}), ("news", {"source": "local"})])
async def test_ingestion_rejects_anonymous(client, kind, body):
    r = await client.post(f"/api/v1/ingest/{kind}", json=body)
    assert r.status_code == 401, f"/ingest/{kind} must require auth, got {r.status_code}"
