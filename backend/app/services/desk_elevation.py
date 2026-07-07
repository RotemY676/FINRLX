"""Desk W1 — API-7 elevation rule (SPEC-02 \u00A72, QS-2 compliant).

Pure function over signal-matrix rows. Selects the top-3 "most statistically
unusual" signals for Panel A. This is a RANKING OF UNUSUALNESS, never a
prediction; the fixed caption and the verbatim method disclosure below are
part of the contract and are surfaced in the panel's Forensic drawer.

Normative algorithm (SPEC-02 API-7):
  1. Eligible = rows with a numeric ``percentile`` (i.e. \u2265252 sessions of
     own history). Ineligible rows can never be elevated.
  2. Unusualness  u = |percentile\u00d7100 \u2212 50| \u00d7 2            (range 0\u2013100)
  3. Regime weight w = 1.15 when the row's family matches the current
     regime label, else 1.0. The family map is the fixed constant below.
  4. Score s = u \u00d7 w; take top-3 by s; ties break by FEATURE_PRIORITY
     order (lower index wins).
  5. If no rows are eligible, elevation is omitted with an honest note.
"""
from __future__ import annotations

CAPTION = "most statistically unusual for this stock \u2014 not a prediction"

# Fixed family map (printed verbatim in the drawer): key-prefix -> family.
FAMILY_PREFIXES: dict[str, str] = {
    "return_": "momentum",
    "sma": "momentum",
    "macd": "momentum",
    "volatility_": "risk",
    "drawdown_": "risk",
    "turbulence": "risk",
    "rsi": "mean_reversion",
}

# Regime label -> favored family (uptrend favors momentum; risk-off favors
# the risk family; neutral favors mean-reversion).
REGIME_FAMILY: dict[str, str] = {
    "uptrend": "momentum",
    "risk-off": "risk",
    "neutral": "mean_reversion",
}

REGIME_WEIGHT = 1.15

# Deterministic tie-break order (lower index wins). Any key not listed
# ranks after all listed keys, alphabetically.
FEATURE_PRIORITY: list[str] = [
    "volatility_20d",
    "drawdown_20d",
    "return_5d",
    "return_20d",
    "return_60d",
    "rsi_14",
    "macd",
]


def _family(key: str) -> str | None:
    for prefix, fam in FAMILY_PREFIXES.items():
        if key.startswith(prefix):
            return fam
    return None


def _priority(key: str) -> tuple[int, str]:
    try:
        return (FEATURE_PRIORITY.index(key), key)
    except ValueError:
        return (len(FEATURE_PRIORITY), key)


def elevate(rows: list[dict], regime_label: str) -> dict:
    """Return the elevation block for the technical section payload.

    Output (always well-formed, never raises on odd rows):
      { "elevated": [key, key, key],          # \u22643, may be []
        "caption": CAPTION,
        "method": {\u2026verbatim disclosure\u2026},
        "note": str | None }                  # set when nothing eligible
    """
    favored = REGIME_FAMILY.get(regime_label)
    scored: list[tuple[float, tuple[int, str], str]] = []
    for row in rows:
        p = row.get("percentile")
        key = row.get("key")
        if not isinstance(p, int | float) or not isinstance(key, str):
            continue  # ineligible: no percentile => never elevated
        u = abs(p * 100.0 - 50.0) * 2.0
        w = REGIME_WEIGHT if (favored and _family(key) == favored) else 1.0
        scored.append((u * w, _priority(key), key))
    scored.sort(key=lambda t: (-t[0], t[1]))
    elevated = [k for _, _, k in scored[:3]]
    return {
        "elevated": elevated,
        "caption": CAPTION,
        "method": {
            "summary": (
                "Signals are ranked by how unusual their current value is "
                "versus this stock's own history; the current regime's "
                "signal family gets a small weight. This ranks unusualness "
                "\u2014 it does not predict returns."
            ),
            "formula": "score = |percentile\u00d7100 \u2212 50| \u00d7 2 \u00d7 "
                       f"(regime-family weight {REGIME_WEIGHT} else 1.0)",
            "family_map": FAMILY_PREFIXES,
            "regime_family": REGIME_FAMILY,
            "tie_break": FEATURE_PRIORITY,
            "eligibility": "requires \u2265252 sessions of own history "
                           "(percentile present); others can never be elevated",
        },
        "note": None if elevated else
                "no signal has enough history for percentile ranking yet",
    }
