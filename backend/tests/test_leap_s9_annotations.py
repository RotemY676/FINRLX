"""Program LEAP S9 — annotation contract tests (gates G8.1 adversarial
validator, G8.2 flag-off regression, canary behavior)."""
from __future__ import annotations

from unittest import mock

import pytest

from app.services import news_annotations as na

SOURCE = {
    "item_id": "n-1",
    "published_at": "2026-07-01T12:00:00Z",
    "title": "NVDA announces new datacenter product line",
    "summary": "The company detailed capacity plans and pricing for NVDA hardware.",
}


def _candidate(text: str, item_id: str = "n-1", published: str = SOURCE["published_at"]) -> dict:
    return {
        "item_id": item_id,
        "annotation": text,
        "source_binding": {"item_id": item_id, "published_at": published},
        "model": "test:model",
        "generated_at": "2026-07-06T00:00:00Z",
        "freshness_stamp": published,
    }


# ── G8.1: adversarial validator ─────────────────────────────────────────────


def test_valid_two_sentence_annotation_passes():
    cand = _candidate(
        "New capacity plans affect NVDA supply expectations. Pricing details "
        "give researchers a concrete input for margin analysis."
    )
    assert na.validate_annotation(cand, SOURCE) is None


def test_missing_source_binding_rejected():
    cand = _candidate("Relevant detail about NVDA capacity.")
    cand["source_binding"] = {}
    rej = na.validate_annotation(cand, SOURCE)
    assert rej and rej.reason == "missing_or_mismatched_source_binding"


def test_mismatched_item_id_rejected():
    cand = _candidate("Relevant detail about NVDA capacity.", item_id="n-999")
    rej = na.validate_annotation(cand, SOURCE)
    assert rej and rej.reason == "missing_or_mismatched_source_binding"


def test_published_at_mismatch_rejected():
    cand = _candidate("Relevant detail about NVDA capacity.",
                      published="2026-01-01T00:00:00Z")
    assert na.validate_annotation(cand, SOURCE).reason == "published_at_mismatch"


def test_three_sentences_rejected():
    cand = _candidate("One. Two. Three about NVDA.")
    assert na.validate_annotation(cand, SOURCE).reason == "too_many_sentences"


@pytest.mark.parametrize("bad", [
    "This means you should buy NVDA now.",
    "The stock will outperform its peers.",
    "A guaranteed catalyst for the quarter.",
    "Investors must act now on this news.",
    "Sell before the announcement lands.",
])
def test_advice_language_rejected(bad):
    assert na.validate_annotation(_candidate(bad), SOURCE).reason == "advice_language"


def test_ticker_not_in_source_rejected():
    cand = _candidate("This capacity shift also pressures AMD margins.")
    rej = na.validate_annotation(cand, SOURCE)
    assert rej and rej.reason.startswith("unbound_tickers:") and "AMD" in rej.reason


def test_acronym_stopwords_not_treated_as_tickers():
    cand = _candidate("The SEC filing gives GDP-adjusted context for NVDA plans.")
    assert na.validate_annotation(cand, SOURCE) is None


def test_empty_annotation_rejected():
    assert na.validate_annotation(_candidate("   "), SOURCE).reason == "empty_annotation"


# ── canary ──────────────────────────────────────────────────────────────────


def test_canary_all_valid_passes():
    cands = [_candidate("Concrete NVDA supply detail for researchers.")] * 5
    ok, rej = na.run_canary(cands, {"n-1": SOURCE})
    assert ok and rej == []


def test_canary_single_bad_fails_whole_batch():
    cands = [
        _candidate("Concrete NVDA supply detail for researchers."),
        _candidate("You should buy NVDA."),
    ]
    ok, rej = na.run_canary(cands, {"n-1": SOURCE})
    assert not ok
    assert rej[0].reason == "advice_language"


def test_canary_unknown_source_fails():
    ok, rej = na.run_canary([_candidate("Detail.", item_id="ghost")], {"n-1": SOURCE})
    assert not ok and rej[0].reason in ("unknown_source", "missing_or_mismatched_source_binding")


# ── G8.2: flag/provider gating (async annotator) ────────────────────────────


@pytest.mark.asyncio
async def test_flag_off_returns_untouched_status():
    from app.core.config import settings

    with mock.patch.object(settings, "insights_annotations", False):
        out = await na.annotate_items("NVDA", [SOURCE])
    assert out == {"status": "flag_off", "annotations": [], "rejections": []}


@pytest.mark.asyncio
async def test_flag_on_without_provider_is_honest():
    from app.core.config import settings

    with mock.patch.object(settings, "insights_annotations", True), mock.patch.object(
        na, "get_provider", return_value=None
    ):
        out = await na.annotate_items("NVDA", [SOURCE])
    assert out["status"] == "provider_unconfigured"
    assert out["annotations"] == []


@pytest.mark.asyncio
async def test_flag_on_with_provider_generates_validated_annotations():
    from app.core.config import settings

    class FakeProvider:
        name, model = "fake", "fake-1"

        async def chat(self, messages, *, max_tokens=1024, temperature=0.2):
            class R:  # minimal LLMResponse stand-in
                content = ("Capacity plans give NVDA researchers a supply-side "
                           "input. Pricing details anchor margin scenarios.")
            return R()

    with mock.patch.object(settings, "insights_annotations", True), mock.patch.object(
        na, "get_provider", return_value=FakeProvider()
    ):
        out = await na.annotate_items("NVDA", [SOURCE])
    assert out["status"] == "ok"
    assert len(out["annotations"]) == 1
    ann = out["annotations"][0]
    assert ann["source_binding"] == {"item_id": "n-1", "published_at": SOURCE["published_at"]}
    assert ann["model"] == "fake:fake-1"
    assert ann["freshness_stamp"] == SOURCE["published_at"]


@pytest.mark.asyncio
async def test_provider_emitting_advice_fails_canary_and_ships_nothing():
    from app.core.config import settings

    class AdviceProvider:
        name, model = "fake", "fake-1"

        async def chat(self, messages, *, max_tokens=1024, temperature=0.2):
            class R:
                content = "You should buy NVDA immediately."
            return R()

    with mock.patch.object(settings, "insights_annotations", True), mock.patch.object(
        na, "get_provider", return_value=AdviceProvider()
    ):
        out = await na.annotate_items("NVDA", [SOURCE])
    assert out["status"] == "canary_failed"
    assert out["annotations"] == []
    assert out["rejections"][0]["reason"] == "advice_language"


# ── dossier integration (S9 -> S2 News card) ────────────────────────────────


@pytest.mark.asyncio
async def test_dossier_flag_off_shape_untouched(monkeypatch):
    from app.services import autopilot_store as store

    dossier = {"ticker": "T1", "sections": {"news_sentiment": {"items_7d": [
        {"date": "2026-07-01", "title": "T1 update"}]}}}
    await store._attach_annotations(dossier)
    item = dossier["sections"]["news_sentiment"]["items_7d"][0]
    assert dossier["sections"]["news_sentiment"]["annotations_status"] == "flag_off"
    assert "why_this_matters" not in item


@pytest.mark.asyncio
async def test_dossier_gains_annotations_when_all_gates_pass(monkeypatch):
    from app.core.config import settings
    from app.services import autopilot_store as store

    class FakeProvider:
        name, model = "fake", "fake-1"

        async def chat(self, messages, *, max_tokens=1024, temperature=0.2):
            class R:
                content = "Capacity news gives T2 researchers a concrete supply input."
            return R()

    dossier = {"ticker": "T2", "sections": {"news_sentiment": {"items_7d": [
        {"date": "2026-07-01", "title": "T2 capacity news"}]}}}
    with mock.patch.object(settings, "insights_annotations", True), mock.patch.object(
        na, "get_provider", return_value=FakeProvider()
    ):
        await store._attach_annotations(dossier)
    news = dossier["sections"]["news_sentiment"]
    assert news["annotations_status"] == "ok"
    item = news["items_7d"][0]
    assert "supply input" in item["why_this_matters"]
    assert item["annotation_meta"]["model"] == "fake:fake-1"
    assert item["annotation_meta"]["freshness_stamp"] == "2026-07-01"
