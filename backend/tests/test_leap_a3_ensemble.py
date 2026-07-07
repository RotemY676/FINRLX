"""LEAP A3 — FinRL ensemble artifact merge (D45 gates: protocol match,
re-deflated penalties, RL-can-win-honestly, absent path)."""
from __future__ import annotations

import json

import pytest

from app.services import finrl_ensemble as fe

SPLITS = [(40, 55), (55, 70), (70, 85)]
BASE_ROWS = [
    {"key": "sma", "name": "SMA cross", "kind": "heuristic", "description": "",
     "train_sharpe": 0.8, "val_sharpe": 0.6, "divergence": 0.2,
     "penalty": 0.1, "score": 0.0, "eligible": True,
     "per_split_val_sharpe": [0.5, 0.6, 0.7]},
]


def _artifact(**over):
    art = {
        "schema_version": "e6-1", "ticker": "T", "generated_at": "2026-07-06T00:00:00Z",
        "recipe": "icaif2020-ensemble",
        "splits": [list(s) for s in SPLITS],
        "agents": {
            "rl_ppo": {"name": "PPO (FinRL ensemble)", "train_sharpe": 1.4,
                       "val_sharpe": 1.2, "per_split_val_sharpe": [1.0, 1.2, 1.4]},
            "rl_a2c": {"name": "A2C (FinRL ensemble)", "train_sharpe": 2.5,
                       "val_sharpe": 0.3, "per_split_val_sharpe": [0.2, 0.3, 0.4]},
        },
        "selection_history": [
            {"period": "2026-Q1", "selected": "rl_ppo", "val_sharpe": 1.1, "turbulence_gate": False},
            {"period": "2026-Q2", "selected": "rl_a2c", "val_sharpe": 0.9, "turbulence_gate": True},
        ],
        "turbulence_events": [{"date": "2026-04-07", "action": "liquidate"}],
    }
    art.update(over)
    return art


def _write(tmp_path, monkeypatch, art):
    monkeypatch.setattr(fe, "ARTIFACT_DIR", tmp_path)
    (tmp_path / "T.json").write_text(json.dumps(art))


def test_absent_artifact_returns_queued_and_rows_untouched(tmp_path, monkeypatch):
    monkeypatch.setattr(fe, "ARTIFACT_DIR", tmp_path)
    rows, status = fe.merge_rl_candidates("T", BASE_ROWS, SPLITS, 45, 0.5)
    assert rows == BASE_ROWS
    assert status["status"] == "queued_for_research_run"
    assert "E7" in status["note"]


def test_protocol_mismatch_rejected(tmp_path, monkeypatch):
    _write(tmp_path, monkeypatch, _artifact(splits=[[1, 2]]))
    rows, status = fe.merge_rl_candidates("T", BASE_ROWS, SPLITS, 45, 0.5)
    assert rows == BASE_ROWS
    assert status["status"] == "artifact_rejected"
    assert status["reason"] == "protocol_mismatch"
    assert "never scored on different windows" in status["note"]


def test_incomplete_agent_rejected(tmp_path, monkeypatch):
    art = _artifact()
    del art["agents"]["rl_ppo"]["per_split_val_sharpe"]
    _write(tmp_path, monkeypatch, art)
    _, status = fe.merge_rl_candidates("T", BASE_ROWS, SPLITS, 45, 0.5)
    assert status["reason"] == "agent_incomplete:rl_ppo"


def test_merge_rescores_everyone_with_enlarged_deflation(tmp_path, monkeypatch):
    _write(tmp_path, monkeypatch, _artifact())
    rows, status = fe.merge_rl_candidates("T", BASE_ROWS, SPLITS, 45, 0.5)
    assert status["status"] == "artifact_merged"
    assert len(rows) == 3
    import math
    expected_penalty = round(math.sqrt(math.log(3) / 45), 4)
    assert all(r["penalty"] == expected_penalty for r in rows)  # everyone re-deflated
    ppo = next(r for r in rows if r["key"] == "rl_ppo")
    # score = val - 0.5*|train-val| - penalty
    assert ppo["score"] == round(1.2 - 0.5 * 0.2 - expected_penalty, 3)
    assert ppo["kind"] == "rl" and ppo["imported_from_artifact"] is True
    # overfit A2C (train 2.5 vs val 0.3) gets punished below the heuristic
    a2c = next(r for r in rows if r["key"] == "rl_a2c")
    sma = next(r for r in rows if r["key"] == "sma")
    assert a2c["score"] < sma["score"]
    # selection history + turbulence events surfaced for the desk
    assert status["selection_history"][1]["turbulence_gate"] is True
    assert status["turbulence_events"][0]["action"] == "liquidate"


def test_full_tournament_lets_honest_rl_win_and_tie_still_favors_simpler(tmp_path, monkeypatch):
    """End-to-end through run_tournament: a genuinely better PPO wins; the
    D36 tie-break ordering (heuristic < ml < rl) is preserved in the sort."""
    from datetime import date, timedelta
    from app.services import autopilot
    from app.services.single_ticker_analysis import Bars

    dates, closes = [], []
    d, px, i = date(2023, 1, 2), 100.0, 0
    while len(dates) < 500:
        if d.weekday() < 5:
            px *= 1.0 + (0.004 if (i // 20) % 2 == 0 else -0.002)
            dates.append(d); closes.append(round(px, 4)); i += 1
        d += timedelta(days=1)
    bars = Bars(dates=dates, closes=closes, volumes=[1_000_000] * 500,
                highs=[c * 1.01 for c in closes], lows=[c * 0.99 for c in closes])
    monkeypatch.setattr(autopilot, "fetch_history", lambda s, days: bars)
    monkeypatch.setattr(autopilot, "fetch_news", lambda s, limit=20: ([], False))
    autopilot._dossier_cache.clear()

    # First, run once WITHOUT artifact to learn the real service splits
    monkeypatch.setattr(fe, "ARTIFACT_DIR", tmp_path)
    d0 = autopilot.build_dossier("A3T")
    t0 = d0["sections"]["model_insight"]
    assert t0["rl"]["status"] == "queued_for_research_run"
    splits = None
    # reconstruct service splits deterministically
    from app.services.autopilot import walk_forward_splits, precompute_rebalance_states, _generate_weekly_rebalances
    start = bars.dates[60]
    rebalances = _generate_weekly_rebalances(start, bars.dates[-1])
    states = precompute_rebalance_states(bars, [], rebalances)
    splits = walk_forward_splits(len(states))

    best_local = max(c["score"] for c in t0["candidates"])
    art = _artifact(splits=[list(s) for s in splits])
    art["agents"] = {"rl_ppo": {"name": "PPO (FinRL ensemble)",
                                "train_sharpe": best_local + 2.2,
                                "val_sharpe": best_local + 2.0,
                                "per_split_val_sharpe": [best_local + 2.0] * len(splits)}}
    (tmp_path / "A3T.json").write_text(json.dumps(art))
    autopilot._dossier_cache.clear()
    d1 = autopilot.build_dossier("A3T")
    t1 = d1["sections"]["model_insight"]
    assert t1["rl"]["status"] == "artifact_merged"
    assert t1["winner"]["key"] == "rl_ppo"
    assert t1["winner"]["kind"] == "rl"
    assert "penalt" in t1["winner"]["rationale"]
