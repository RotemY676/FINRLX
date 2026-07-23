"""US-DPK-02 — snapshot ids are content addresses, not surrogate keys.

The point of a content hash is that lineage becomes *checkable*: the same bars
must produce the same id on any machine and in any process, and one changed
close must produce a different one. A surrogate key records that data existed;
a content hash proves which data it was.
"""
from __future__ import annotations

from datetime import date

from app.services.snapshot_manifest import (
    compute_data_snapshot_id,
    compute_feature_snapshot_id,
    snapshot_manifest,
)

CUTOFF = date(2026, 7, 22)


def _bars():
    return [
        {"ticker": "AAA", "bar_date": date(2026, 7, 20), "close": 10.0, "source": "yfinance"},
        {"ticker": "AAA", "bar_date": date(2026, 7, 21), "close": 10.5, "source": "yfinance"},
        {"ticker": "BBB", "bar_date": date(2026, 7, 21), "close": 99.0, "source": "yfinance"},
    ]


def _features():
    return [
        {"asset_id": "a1", "feature_key": "rsi_14", "value": 55.2, "quality": "ok"},
        {"asset_id": "a1", "feature_key": "return_5d", "value": 0.01, "quality": "ok"},
    ]


def test_the_same_bars_always_produce_the_same_id():
    assert compute_data_snapshot_id(_bars(), cutoff=CUTOFF) == compute_data_snapshot_id(
        _bars(), cutoff=CUTOFF
    )


def test_row_order_does_not_change_the_id():
    shuffled = list(reversed(_bars()))
    assert compute_data_snapshot_id(shuffled, cutoff=CUTOFF) == compute_data_snapshot_id(
        _bars(), cutoff=CUTOFF
    )


def test_one_changed_close_changes_the_id():
    changed = _bars()
    changed[1]["close"] = 10.51
    assert compute_data_snapshot_id(changed, cutoff=CUTOFF) != compute_data_snapshot_id(
        _bars(), cutoff=CUTOFF
    )


def test_the_provider_is_part_of_the_identity():
    """The same close from a different source is a different evidentiary claim
    — the zero-fiction source allowlist depends on that distinction."""
    other = _bars()
    other[0]["source"] = "local_deterministic"
    assert compute_data_snapshot_id(other, cutoff=CUTOFF) != compute_data_snapshot_id(
        _bars(), cutoff=CUTOFF
    )


def test_the_cutoff_is_part_of_the_identity():
    """A cutoff is a claim about what was knowable at the time."""
    assert compute_data_snapshot_id(_bars(), cutoff=date(2026, 7, 23)) != (
        compute_data_snapshot_id(_bars(), cutoff=CUTOFF)
    )


def test_no_data_yields_no_id_rather_than_the_hash_of_nothing():
    """A packet with no data must carry no snapshot id, not a valid-looking one."""
    assert compute_data_snapshot_id([], cutoff=CUTOFF) is None
    assert compute_feature_snapshot_id([], cutoff=CUTOFF) is None


def test_rows_without_an_identity_are_ignored():
    junk = [{"ticker": None, "bar_date": None, "close": 1.0, "source": "x"}]
    assert compute_data_snapshot_id(junk, cutoff=CUTOFF) is None


def test_a_definition_change_changes_the_feature_snapshot():
    """Same inputs under a changed definition are not the same features."""
    a = compute_feature_snapshot_id(_features(), cutoff=CUTOFF, definitions_version="v1")
    b = compute_feature_snapshot_id(_features(), cutoff=CUTOFF, definitions_version="v2")
    assert a != b


def test_ids_are_prefixed_so_the_two_kinds_cannot_be_confused():
    data_id = compute_data_snapshot_id(_bars(), cutoff=CUTOFF)
    feat_id = compute_feature_snapshot_id(_features(), cutoff=CUTOFF)
    assert data_id.startswith("data:")
    assert feat_id.startswith("feat:")


def test_the_manifest_reports_the_algorithm_it_used():
    m = snapshot_manifest(
        bars=_bars(), features=_features(), cutoff=CUTOFF, definitions_version="v1"
    )
    assert m["algo"] == "sha256-canonical-v1"
    assert m["data_snapshot_id"].startswith("data:")
    assert m["feature_snapshot_id"].startswith("feat:")
    assert m["bar_count"] == 3


def test_the_adapter_declares_which_kind_of_id_each_field_carries():
    """A surrogate key must not read as a content hash.

    The legacy pipeline supplies one of each: input_hash is reproducible from
    the signal rows, source_feature_set_id is a row id that proves a feature
    set existed but not which values it held.
    """
    from app.models.recommendation import Recommendation
    from app.services.decision_packet_adapter import _build_lineage

    rec = Recommendation(
        input_hash="abc123",
        source_feature_set_id="fs-1",
        policy_hash="p1",
        pipeline_version="v1",
    )
    lineage = _build_lineage(rec)
    assert lineage.data_snapshot_kind == "content_hash"
    assert lineage.feature_snapshot_kind == "surrogate_id"


def test_absent_ids_are_declared_unavailable_not_silently_blank():
    from app.models.recommendation import Recommendation
    from app.services.decision_packet_adapter import _build_lineage

    lineage = _build_lineage(Recommendation())
    assert lineage.data_snapshot_kind == "unavailable"
    assert lineage.feature_snapshot_kind == "unavailable"


def test_object_rows_hash_the_same_as_mapping_rows():
    """Callers pass ORM rows or dicts; identity must not depend on which."""

    class Row:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    objs = [Row(**b) for b in _bars()]
    assert compute_data_snapshot_id(objs, cutoff=CUTOFF) == compute_data_snapshot_id(
        _bars(), cutoff=CUTOFF
    )
