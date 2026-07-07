"""Desk W1 — API-6 additive ``method`` blocks (SPEC-02 \u00A72).

Every D42 section response gains a ``method`` object powering the Forensic
drawer's three-part anatomy: plain summary \u2192 contributing factors \u2192 full
detail, plus per-source freshness. Additive-only: no existing consumer
breaks; the Desk v2 client requires it.

Honesty rules: summaries describe what WAS computed for this dossier (not
marketing); every factor names a real input; sources come from the
dossier's own freshness/section holders \u2014 nothing is invented here.
"""
from __future__ import annotations


def _sources_price(dossier: dict) -> list[dict]:
    fresh = dossier.get("freshness") or {}
    return [{
        "name": "price provider chain (yfinance\u2192stooq, coverage-aware)",
        "as_of": fresh.get("latest_bar"),
        "coverage": f"{fresh.get('bars', 0)} bars",
    }]


def _factors(items: list[tuple[str, str]]) -> list[dict]:
    return [{"name": n, "role": r} for n, r in items]


def _m(summary: str, factors: list[dict], detail: str, sources: list[dict]) -> dict:
    return {"summary": summary, "factors": factors,
            "detail_md": detail, "sources": sources}


def method_block(section: str, dossier: dict) -> dict | None:
    """Method object for a D42 section, or None for sections without one."""
    ns = (dossier.get("sections") or {}).get("news_sentiment") or {}
    mi = (dossier.get("sections") or {}).get("model_insight") or {}

    if section in ("signals", "risk"):
        return _m(
            "Each technical signal is compared against this stock's own "
            "trailing history to answer: is today's value unusual for THIS "
            "stock? Percentiles require at least one trading year of history "
            "or they are omitted with a note.",
            _factors([
                ("daily closes (3y window)", "input"),
                ("per-signal rolling recomputation", "input"),
                ("252-session minimum for percentiles", "threshold"),
                ("60-session sparkline window", "input"),
            ]),
            "For every matrix signal the engine recomputes the signal over "
            "each historical prefix, then ranks the current value inside "
            "that distribution (`desk_payload.signal_matrix`). Signals with "
            "fewer than 252 sessions of own history carry "
            "`percentile: null` plus an explicit note \u2014 never a fabricated "
            "rank. Elevation (top-3) ranks unusualness only; its full "
            "formula, family map and tie-break order ship inside the "
            "`elevation.method` object of this payload.",
            _sources_price(dossier),
        )

    if section == "tournament":
        rl = (mi.get("rl") or {}).get("status")
        return _m(
            "Candidate models compete on walk-forward validation: each is "
            "trained on earlier data and scored on later data it never saw, "
            "with penalties for train/validation divergence and for "
            "multiple testing. Ties go to the simpler model.",
            _factors([
                ("expanding train/validation splits (\u22653)", "input"),
                ("validation Sharpe", "input"),
                ("|train \u2212 validation| divergence penalty", "penalty"),
                ("deflated-Sharpe multiple-testing penalty", "penalty"),
                ("simplicity tie-break (heuristic > ML > RL)", "threshold"),
            ]),
            "Scoreboard fields `train_sharpe`, `val_sharpe`, `divergence`, "
            "`deflation_penalty` and `score` are persisted per candidate; "
            "the winner is the highest post-penalty score. "
            + ("The RL leg is currently `queued_for_research_run` (operator "
               "item E7): its candidates enter this scoreboard only after "
               "real training in the isolated research container \u2014 the desk "
               "never simulates their output. " if rl == "queued_for_research_run" else "")
            + "RL candidates are research models and are permanently barred "
              "from the governed recommendation pipeline (D18/D30).",
            _sources_price(dossier),
        )

    if section == "news_social":
        lane = ns.get("social") or {}
        scored = not (lane.get("available") is False
                      or lane.get("label") == "mentions only, unscored")
        return _m(
            "Two independent sentiment lanes: the news lane scores each "
            "article; the social lane tracks platform mentions"
            + (" with scores" if scored else
               " (mentions-only fallback until the scored tier is enabled)")
            + ". When the lanes disagree in sign beyond threshold, the desk "
              "raises a divergence flag instead of averaging the "
              "disagreement away.",
            _factors([
                ("per-article sentiment (news lane)", "input"),
                ("platform mentions" + ("+scores" if scored else " (unscored)"), "input"),
                ("sign-based lane divergence", "threshold"),
            ]),
            "News items carry per-item labels and compounds; the social "
            "lane is always explicitly labeled with its mode. Divergence "
            "compares the news-lane average sign with the social-lane sign "
            "(`compute_divergence`); with a mentions-only fallback, "
            "divergence honestly reports `not_applicable` rather than "
            "inventing a score.",
            [{"name": "news feed", "as_of": dossier.get("generated_at"),
              "coverage": f"{(ns.get('counts') or {}).get('news_count_7d', 'n/a')} items / 7d"},
             {"name": lane.get("source") or "social lane",
              "as_of": dossier.get("generated_at"),
              "coverage": lane.get("label") or ("scored" if scored else "fallback")}],
        )

    if section in ("fundamentals", "filings", "insider"):
        holder = (dossier.get("sections") or {}).get(section) or {}
        return _m(
            {"fundamentals": "Revenue, margin and EPS trends are read "
                             "directly from the company's own XBRL facts as "
                             "filed with the SEC.",
             "filings": "Filing tone and similarity deltas compare the "
                        "language of consecutive filings to surface "
                        "material drift.",
             "insider": "Insider signal aggregates officers'/directors' "
                        "transaction sentiment (MSPR) over the trailing "
                        "months."}[section],
            _factors([("SEC XBRL company facts" if section == "fundamentals"
                       else "Finnhub " + section + " feed", "input")]),
            "Section availability is a first-class field: when the source "
            "is down the payload says so (`available: false` + reason) and "
            "the desk renders that state \u2014 values are never synthesized.",
            [{"name": "SEC EDGAR/XBRL (keyless)" if section == "fundamentals"
              else "Finnhub", "as_of": dossier.get("generated_at"),
              "coverage": "available" if holder.get("available") else
                          str(holder.get("reason") or "unavailable")}],
        )

    if section in ("chart", "header"):
        return _m(
            "Prices come from the coverage-aware provider chain; every bar "
            "is stamped with its source, and every surface renders the "
            "same series (one-price-truth).",
            _factors([
                ("provider chain (deepest coverage wins)", "input"),
                ("regime rule (SMA20/50 + 20d drawdown)", "input"),
                ("evidence-linked event markers", "input"),
            ]),
            "The chart endpoint is contract-tested to equal the dossier's "
            "`price_series` exactly (K1). Regime bands reuse the production "
            "regime rule verbatim (rule-parity-tested); each event marker "
            "carries an `evidence_ref` to its source document.",
            _sources_price(dossier),
        )

    return None
