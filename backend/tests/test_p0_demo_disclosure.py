"""US-P0-06 follow-up — a demo label must reach a user, not just a payload.

Review finding 2026-07-23: `/scenario/simulate` returns figures built from
hardcoded constants and invented sensitivity coefficients. It was correctly
marked `is_demo=True`, so `meta.warnings` carried the DEMO_DATA label — and no
surface rendered it. The card showed the *data-level* warnings instead, which
for that endpoint include a fabricated statistical claim ("exceeds historical
1σ range" computed from no distribution). The one honest warning was the only
one discarded.

The lesson is that labelling and disclosing are different things, and only the
second protects the reader. These tests pin both halves.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.api.deps import DEMO_DATA_WARNING
from app.core.fiction_policy import (
    KNOWN_FICTION_SITES,
    classify_fiction,
    scan_fiction_risks,
)

FRONTEND = Path(__file__).resolve().parents[2] / "frontend" / "src"


def test_every_demo_route_is_triaged():
    """A route serving seeded data must be reviewed, not merged silently."""
    result = classify_fiction(scan_fiction_risks())
    assert result["unclassified"] == [], (
        "new fabrication/demo sites in serving paths: " + ", ".join(result["unclassified"])
    )


def test_every_demo_route_records_where_its_disclosure_lives():
    """Acceptance of a demo route requires naming the user-visible disclosure.

    Without this, "is_demo=True" reads as protection when it may be inert.
    """
    demo_sites = {
        f.location for f in scan_fiction_risks() if f.category == "demo-route"
    }
    assert demo_sites, "expected at least one demo route to be enumerated"
    for site in demo_sites:
        justification = KNOWN_FICTION_SITES.get(site, "")
        assert "DISCLOSURE" in justification or "disclosure" in justification, (
            f"{site} is accepted as a demo route without naming where the user "
            "sees that. A label no surface renders is not a disclosure."
        )


@pytest.mark.skipif(not FRONTEND.exists(), reason="frontend tree not present")
def test_the_scenario_card_actually_renders_the_demo_notice():
    """Guard the specific regression: meta dropped, notice gone.

    Asserted against the source rather than a mock because the failure mode was
    structural — the component never kept `meta` in the first place.
    """
    card = (FRONTEND / "components" / "decision" / "ScenarioCard.tsx").read_text(
        encoding="utf-8"
    )
    assert "res.meta" in card, (
        "ScenarioCard must keep meta; dropping it is what silenced the demo label"
    )
    assert "scenario-demo-notice" in card, "the visible notice is missing"
    assert "DEMO_DATA" in card, "the notice must key off the backend's label"


def test_the_demo_label_constant_is_machine_parseable():
    """Consumers key off the prefix; it must stay stable and prefixed."""
    assert DEMO_DATA_WARNING.startswith("DEMO_DATA:")
