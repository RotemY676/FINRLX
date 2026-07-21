"""Shared API dependencies."""
from datetime import UTC, datetime

from app.schemas.common import FreshnessState, ResponseMeta

# US-P0-06 zero-fiction: standardized, machine-parseable label for endpoints that
# serve seeded/illustrative data rather than a live model output. Demo data must
# be explicitly labeled so a consumer can never mistake it for real evidence.
DEMO_DATA_WARNING = "DEMO_DATA: seeded illustrative data, not a live model output"


def make_meta(
    warnings: list[str] | None = None,
    *,
    is_demo: bool = False,
    freshness: FreshnessState | None = None,
) -> ResponseMeta:
    ws = list(warnings or [])
    if is_demo and DEMO_DATA_WARNING not in ws:
        ws.insert(0, DEMO_DATA_WARNING)
    return ResponseMeta(
        api_version="v1",
        generated_at=datetime.now(UTC),
        warnings=ws,
        freshness=freshness,
    )
