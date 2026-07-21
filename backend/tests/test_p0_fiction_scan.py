"""US-P0-06 — zero-fiction static scan + one-way ratchet.

Every fabrication primitive (``random``/``numpy.random`` draw, or a
fiction-admitting TODO) in the serving paths (``app/api``, ``app/services``) is
either absent or recorded, with a justification, in ``KNOWN_FICTION_SITES``. The
core invariant is that the ``unclassified`` bucket is empty: a NEW fabrication
site cannot be merged without being explicitly triaged. The baseline may only
shrink — fixing a site removes both the code and its entry.

This is the repo-wide static scan the delta doc recorded as missing. It does not
by itself prove that labeled-synthetic ingest data is failed closed downstream
(that end-to-end linkage is the US-P0-06 follow-up); it forward-locks the
fabrication surface so no *new*, unreviewed fiction can appear.
"""
from __future__ import annotations

from app.core.fiction_policy import (
    FICTION_SCAN_BASELINE,
    KNOWN_FICTION_SITES,
    classify_fiction,
    scan_fiction_risks,
)


def test_no_unclassified_fiction_site():
    """The enforcement gate: no fabrication site outside the reviewed baseline.

    If this fails, a `random`/`np.random` draw or a fake/mock/placeholder TODO
    appeared in a serving path. Either remove it, or — if it is genuinely
    acceptable (non-serving, or labeled-synthetic and downstream-gated) — add it
    to KNOWN_FICTION_SITES with a justification.
    """
    split = classify_fiction(scan_fiction_risks())
    assert split["unclassified"] == [], (
        "Untriaged fabrication sites in serving paths: "
        + ", ".join(split["unclassified"])
    )


def test_baseline_has_no_stale_entries():
    """Every baseline entry must still correspond to a real, found site.

    Forces removal-on-fix: once the code is gone, its baseline entry must go too,
    so the count stays honest and can only shrink.
    """
    found = {f.location for f in scan_fiction_risks()}
    stale = sorted(FICTION_SCAN_BASELINE - found)
    assert stale == [], f"stale KNOWN_FICTION_SITES entries (remove them): {stale}"


def test_every_baseline_entry_has_a_justification():
    """No silent acceptance — each accepted site carries a non-empty reason."""
    missing = sorted(k for k, v in KNOWN_FICTION_SITES.items() if not v.strip())
    assert missing == [], f"baseline entries lacking justification: {missing}"
    # the derived set and the documented dict must agree
    assert FICTION_SCAN_BASELINE == frozenset(KNOWN_FICTION_SITES)


def test_scan_is_deterministic():
    """Two scans return identical, sorted results (safe for CI diffing)."""
    a = scan_fiction_risks()
    b = scan_fiction_risks()
    assert [f.location for f in a] == [f.location for f in b]
    assert a == sorted(a, key=lambda f: (f.location, f.category))
