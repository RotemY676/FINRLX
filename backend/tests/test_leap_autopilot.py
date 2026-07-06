"""PROGRAM LEAP S2/S4 — Autopilot + tournament test suite.

Covers the council-mandated invariants:
- Quant Skeptic: split construction leaks nothing; a deliberately
  overfit candidate is penalized below a stable one; scores reproducible.
- Truthfulness Auditor: disclaimers present; RL leg degrades honestly;
  degraded news is labeled, not hidden; isolation (no recommendation
  tables touched — the module imports none).
- Security/Ops: hostile ticker input rejected server-side.
- UX/product: endpoint contract shape; warm cache path.
"""
from __future__ import annotations

import random
from datetime import date, timedelta

import pytest

from app.services import autopilot
from app.services.autopilot import (
    Candidate,
    build_dossier,
    run_tournament,
    validate_ticker,
    walk_forward_splits,
)
from app.services.single_ticker_analysis import (
    Bars,
    NewsItem,
    _generate_weekly_rebalances,
    precompute_rebalance_states,
)


# ── Fixtures: synthetic market ───────────────────────────────────────────────

def make_bars(n_days: int = 600, seed: int = 7, drift: float = 0.0004) -> Bars:
    rng = random.Random(seed)
    start = date(2024, 1, 2)
    dates, closes, volumes = [], [], []
    px = 100.0
    d = start
    while len(dates) < n_days:
        if d.weekday() < 5:
            px *= 1 + drift + rng.gauss(0, 0.015)
            dates.append(d)
            closes.append(round(px, 4))
            volumes.append(int(1e6 * (1 + rng.random())))
        d += timedelta(days=1)
    highs = [c * 1.01 for c in closes]
    lows = [c * 0.99 for c in closes]
    return Bars(dates=dates, closes=closes, volumes=volumes, highs=highs, lows=lows)


def make_states(bars: Bars):
    rebalances = _generate_weekly_rebalances(bars.dates[60], bars.dates[-1])
    return precompute_rebalance_states(bars, [], rebalances)


@pytest.fixture()
def states():
    return make_states(make_bars())


def _patch_market(monkeypatch, bars: Bars, news: list[NewsItem] | None = None,
                  news_ok: bool = True):
    monkeypatch.setattr(autopilot, "fetch_history", lambda sym, days: bars)
    monkeypatch.setattr(autopilot, "fetch_news", lambda sym, limit=20: (news or [], news_ok))
    autopilot._dossier_cache.clear()


# ── D40: hostile input ───────────────────────────────────────────────────────

@pytest.mark.parametrize("bad", [
    "", "  ", "AAPL; DROP TABLE assets", "../etc/passwd", "NVDA OR 1=1",
    "TOO_LONG_TICKER_X", "nv da", "$NVDA", "NV'DA",
])
def test_hostile_ticker_rejected(bad):
    with pytest.raises(ValueError):
        validate_ticker(bad)


@pytest.mark.parametrize("ok,expect", [("nvda", "NVDA"), (" BRK.B ", "BRK.B"), ("TA35.TA", "TA35.TA")])
def test_valid_ticker_normalized(ok, expect):
    assert validate_ticker(ok) == expect


# ── D36: split construction — leakage impossible by construction ────────────

def test_walk_forward_splits_are_strictly_forward_and_disjoint():
    splits = walk_forward_splits(100)
    assert len(splits) >= 2
    prev_val_end = 0
    for train_end, val_end in splits:
        assert train_end < val_end
        assert train_end >= prev_val_end or prev_val_end == 0
        # validation windows never overlap
        assert train_end >= prev_val_end - 0
        prev_val_end = val_end
    # expanding: each train_end is the previous val boundary
    for (t1, v1), (t2, _v2) in zip(splits, splits[1:]):
        assert t2 == v1


def test_splits_refuse_insufficient_history():
    assert walk_forward_splits(10) == []


def test_ml_fit_uses_only_train_pairs(states, monkeypatch):
    """The ML candidate's training pairs must all lie inside the train slice."""
    seen_dates = []
    orig = autopilot._state_feature_vector

    def spy(st):
        seen_dates.append(st.date)
        return orig(st)

    monkeypatch.setattr(autopilot, "_state_feature_vector", spy)
    splits = walk_forward_splits(len(states))
    train_end, val_end = splits[0]
    fit = autopilot._make_ml_fit()
    decide = fit(states[:train_end])
    train_boundary = states[train_end - 1].date
    assert seen_dates and max(seen_dates) <= train_boundary
    # predictions on validation states are allowed to read the val state itself
    seen_dates.clear()
    decide(states[train_end])
    assert seen_dates == [states[train_end].date]


# ── D36: overfitting guard — a memorizer must lose to a stable model ────────

def test_overfit_candidate_penalized_below_stable_one(states, monkeypatch):
    splits = walk_forward_splits(len(states))
    train_cutoffs = {states[t - 1].date for t, _ in splits}
    max_train = max(train_cutoffs)

    def overfit_decide_factory():
        rng = random.Random(1)
        def decide(st):
            # "Perfect" in-sample (rides every up-move it has memorized),
            # coin-flip out-of-sample: the classic overfit signature.
            if st.date <= max_train:
                return 1.0
            return 1.0 if rng.random() < 0.5 else 0.0
        return decide

    stable = Candidate("stable", "Stable modest", "heuristic", "always 60% long",
                       decide=lambda st: 0.6)
    overfit = Candidate("memorizer", "Overfit memorizer", "ml", "train-perfect, val-random",
                        decide=overfit_decide_factory())

    monkeypatch.setattr(autopilot, "build_candidates", lambda: [stable, overfit])
    result = run_tournament(states)
    rows = {r["key"]: r for r in result["candidates"]}
    assert rows["memorizer"]["divergence"] >= rows["stable"]["divergence"]
    assert result["winner"]["key"] == "stable"
    # penalty decomposition is visible (D37)
    assert result["deflation_penalty"] > 0
    assert "rationale" in result["winner"]


def test_tournament_deterministic(states):
    r1 = run_tournament(states)
    r2 = run_tournament(states)
    assert [c["score"] for c in r1["candidates"]] == [c["score"] for c in r2["candidates"]]
    assert r1["winner"]["key"] == r2["winner"]["key"]


def test_tie_breaks_toward_simpler_model(states, monkeypatch):
    same = lambda st: 0.5  # noqa: E731
    a = Candidate("zz_ml", "ML twin", "ml", "", decide=same)
    b = Candidate("aa_heur", "Heuristic twin", "heuristic", "", decide=same)
    monkeypatch.setattr(autopilot, "build_candidates", lambda: [a, b])
    result = run_tournament(states)
    assert result["winner"]["key"] == "aa_heur"


# ── D35: RL leg degrades honestly ────────────────────────────────────────────

def test_rl_leg_honest_degradation(states):
    result = run_tournament(states)
    rl = result["rl"]
    assert rl["status"] in ("queued_for_research_run", "available")
    if rl["status"] == "queued_for_research_run":
        assert rl["eligible"] is False
        assert "research" in rl["note"].lower()


# ── Dossier pipeline (S2) ────────────────────────────────────────────────────

def test_dossier_full_shape_and_disclaimers(monkeypatch):
    _patch_market(monkeypatch, make_bars())
    d = build_dossier("TEST")
    assert d["ticker"] == "TEST"
    for section in ("technical", "news_sentiment", "fundamentals", "model_insight"):
        assert section in d["sections"]
    assert d["summary"]["stance"] in ("buy", "hold", "sell")
    assert "not investment advice" in " ".join(d["disclaimers"]).lower() or \
           "not advice" in d["summary"]["stance_kind"]
    assert d["sections"]["model_insight"]["status"] == "complete"
    assert d["sections"]["model_insight"]["winner"] is not None
    stage_names = [s["stage"] for s in d["stages"]]
    assert any("ingest" in s for s in stage_names)
    assert any("tournament" in s for s in stage_names)
    assert all("ms" in s for s in d["stages"])


def test_dossier_news_degradation_is_labeled(monkeypatch):
    _patch_market(monkeypatch, make_bars(), news=[], news_ok=False)
    d = build_dossier("TEST")
    ns = d["sections"]["news_sentiment"]
    assert ns["available"] is False
    assert "degraded" in (ns["note"] or "").lower()
    assert d["sections"]["model_insight"]["status"] == "complete"


def test_dossier_insufficient_history_is_honest(monkeypatch):
    _patch_market(monkeypatch, make_bars(n_days=80))
    d = build_dossier("TEST")
    mi = d["sections"]["model_insight"]
    assert mi["status"] == "insufficient_history"
    assert mi["winner"] is None


def test_dossier_cache_warm_path(monkeypatch):
    _patch_market(monkeypatch, make_bars())
    d1 = build_dossier("TEST")
    assert d1["served_from_cache"] is False
    d2 = build_dossier("TEST")
    assert d2["served_from_cache"] is True
    assert d2["sections"]["model_insight"]["winner"]["key"] == \
           d1["sections"]["model_insight"]["winner"]["key"]


# ── Endpoint contract ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_endpoint_contract(client, monkeypatch):
    _patch_market(monkeypatch, make_bars())
    r = await client.get("/api/v1/autopilot/dossier?ticker=test")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "meta" in body and "duration_ms" in body["meta"]
    assert body["data"]["ticker"] == "TEST"
    assert body["data"]["disclaimers"]


@pytest.mark.asyncio
async def test_endpoint_rejects_hostile_ticker(client):
    r = await client.get("/api/v1/autopilot/dossier?ticker=NV'DA")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_endpoint_maps_no_data_to_502(client, monkeypatch):
    empty = Bars(dates=[], closes=[], volumes=[], highs=[], lows=[])
    monkeypatch.setattr(autopilot, "fetch_history", lambda sym, days: empty)
    r = await client.get("/api/v1/autopilot/dossier?ticker=ZZZZ")
    assert r.status_code == 502


# ── Isolation (D30/D18): module must not import the governed pipeline ───────

def test_autopilot_never_touches_recommendation_pipeline():
    """D30/D18 isolation: the autopilot module must not import the governed
    recommendation machinery. Checked at the import level (docstrings may
    legitimately mention the invariant itself)."""
    import ast
    import app.services.autopilot as mod
    tree = ast.parse(open(mod.__file__, encoding="utf-8").read())
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    for forbidden in ("publication", "decision_pipeline", "pipeline"):
        assert not any(forbidden in name for name in imported), (
            f"autopilot must not import {forbidden}: {imported}"
        )
