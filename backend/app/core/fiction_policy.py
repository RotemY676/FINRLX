"""Zero-fiction static scan + one-way ratchet (US-P0-06).

Companion to ``route_policy.py``. Where that module makes every route's *auth*
posture explicit, this module makes the *fabrication* posture of the serving
code explicit: it statically scans the production serving paths for primitives
that can invent financial values out of thin air, and enforces that no *new*
such site can appear without being deliberately triaged.

Two crisp, low-noise categories are detected by AST/text scan:

* ``random`` — a call into the ``random`` module or ``numpy.random`` (any
  ``*.random.*`` attribute chain). These generate values; in a serving path a
  fabricated value could reach a user. Legitimate non-serving uses (research
  stubs, constraint-validation test agents) are recorded in
  ``KNOWN_FICTION_SITES`` with a justification.

* ``todo-fiction`` — a ``TODO``/``FIXME``/``XXX``/``HACK`` comment that admits
  fake/mock/placeholder/synthetic/hardcoded data. This is a pure forward guard
  (currently empty): such a marker may not merge into a serving path unless
  triaged.

The scan is **pure** (no imports of app runtime, no network, no DB) so it runs
in a unit test and can feed an operator listing. Findings are keyed as
``"relpath:lineno"`` with POSIX separators for cross-platform determinism.

Ratchet semantics (enforced by ``tests/test_p0_fiction_scan.py``):
  * no finding outside ``FICTION_SCAN_BASELINE`` (no new fabrication surface);
  * no baseline entry that is no longer found (fix the code → remove the entry).
Together the current fiction surface must exactly equal the reviewed baseline,
so every change to it is a deliberate, reviewed edit.
"""
from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

# Serving paths scanned. Relative to the backend package root (the dir holding
# ``app/``). Data-provider adapters live under app/services and are scanned too:
# a provider that fabricates values is exactly what this guard must catch.
SERVING_ROOTS: tuple[str, ...] = ("app/api", "app/services")

# TODO/FIXME markers that admit fabricated data.
_FICTION_TODO_RE = re.compile(
    r"#.*\b(?:TODO|FIXME|XXX|HACK)\b.*\b"
    r"(?:fake|mock|placeholder|dummy|synthetic|stub|hardcod\w*|made[- ]?up|fabricat\w*)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class FictionFinding:
    """One fabrication-risk site in a serving path."""

    location: str  # "relpath:lineno" (POSIX separators)
    category: str  # "random" | "todo-fiction"
    snippet: str


def backend_root() -> Path:
    """Directory that holds ``app/`` (the backend package root)."""
    # this file is app/core/fiction_policy.py → parents[2] is the backend root.
    return Path(__file__).resolve().parents[2]


def _iter_py_files(base: Path) -> Iterable[Path]:
    for root in SERVING_ROOTS:
        for path in sorted((base / root).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            yield path


def _attr_chain(node: ast.AST) -> list[str]:
    """Return the dotted-name segments of an attribute/name chain, root-first."""
    parts: list[str] = []
    cur: ast.AST | None = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    parts.reverse()
    return parts


def _is_demo_meta_call(node: ast.Call) -> bool:
    """True for ``make_meta(..., is_demo=True)`` — a route serving seeded data.

    Added 2026-07-23 after a review found the scanner's blind spot: it detects
    ``random()`` and fiction-admitting TODOs, but is completely blind to a route
    that returns *hardcoded fabricated constants*. `/scenario/simulate` shipped
    invented baselines and sensitivity coefficients for months; it was correctly
    marked ``is_demo=True`` by US-P0-06, and that label reached no user because
    the card dropped ``meta``.

    Labelling demo data is necessary but not sufficient — the label has to be
    rendered. Enumerating these sites forces each one to record *where* its
    user-visible disclosure lives, so "labelled" can no longer be mistaken for
    "disclosed".
    """
    if _attr_chain(node.func)[-1:] != ["make_meta"]:
        return False
    return any(
        kw.arg == "is_demo"
        and isinstance(kw.value, ast.Constant)
        and kw.value.value is True
        for kw in node.keywords
    )


def _is_random_call(node: ast.Call) -> bool:
    """True if the call target's attribute chain contains a ``random`` segment.

    Catches ``random.uniform(...)``, ``np.random.seed(...)``,
    ``numpy.random.uniform(...)`` — any chain with a ``random`` segment.
    """
    chain = _attr_chain(node.func)
    # need at least ``random.<fn>`` — a bare name ``random(...)`` is not a draw.
    return len(chain) >= 2 and "random" in chain[:-1]


def scan_fiction_risks(base: Path | None = None) -> list[FictionFinding]:
    """Statically scan serving paths; return findings sorted by location."""
    base = base or backend_root()
    findings: list[FictionFinding] = []

    for path in _iter_py_files(base):
        rel = path.relative_to(base).as_posix()
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()

        # AST pass — fabrication primitives.
        try:
            tree = ast.parse(text, filename=rel)
        except SyntaxError:
            # A file that does not parse is a different problem; skip here.
            tree = None
        if tree is not None:
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                ln = node.lineno
                snippet = lines[ln - 1].strip() if 0 < ln <= len(lines) else ""
                if _is_random_call(node):
                    findings.append(
                        FictionFinding(f"{rel}:{ln}", "random", snippet)
                    )
                elif _is_demo_meta_call(node):
                    findings.append(
                        FictionFinding(f"{rel}:{ln}", "demo-route", snippet)
                    )

        # Text pass — fiction-admitting TODO markers.
        for i, line in enumerate(lines, start=1):
            if _FICTION_TODO_RE.search(line):
                findings.append(
                    FictionFinding(f"{rel}:{i}", "todo-fiction", line.strip())
                )

    return sorted(findings, key=lambda f: (f.location, f.category))


# ── Reviewed baseline ─────────────────────────────────────────────────────────
# Fabrication sites that exist today and are ACCEPTED with a recorded reason.
# Each entry carries a justification. This set may only shrink: fixing a site
# means deleting both the code and its entry here.
#
# Two tiers of acceptance are represented:
#   (a) NON-SERVING  — fabrication that can never reach a user (research stubs,
#       test-only agents).
#   (b) LABELED-SYNTHETIC-SOURCE — deterministic synthetic *market data* for the
#       no-provider beta. It DOES enter the data store, so it is only acceptable
#       because it is stamped with the request `source` and MUST be classified
#       `is_synthetic` and failed closed by `decision_truth` before any surfaced
#       decision. Proving that ingest→DataTruth linkage end-to-end is tracked as
#       the US-P0-06 follow-up increment; it is NOT asserted to be complete here.
KNOWN_FICTION_SITES: dict[str, str] = {
    # (c) DEMO-ROUTE — a serving route returning seeded illustrative values.
    #     Acceptance REQUIRES naming the user-visible disclosure. A label in
    #     meta.warnings that no surface renders is not a disclosure: that is
    #     exactly how /scenario/simulate served invented baselines (4.2% weight,
    #     0.74 confidence, 6.4% return) plus invented sensitivity coefficients
    #     on the production /decision page, correctly labelled and completely
    #     unannounced, because ScenarioCard did `setResult(res.data)` and
    #     dropped meta.
    "app/api/v1/scenario.py:127": (
        "POST /scenario/simulate: response is computed from hardcoded BASELINE_* "
        "constants and invented sensitivity coefficients, not a pipeline run. "
        "DISCLOSURE: ScenarioCard renders a visible 'Illustrative only' notice "
        "driven by the DEMO_DATA meta warning (test: scenario-card-demo-notice). "
        "REMOVE THIS ENTRY when the endpoint is rebuilt on the real engine."
    ),
    "app/api/v1/scenario.py:134": (
        "GET /scenario/baseline: the seeded baseline the simulate endpoint "
        "perturbs. Same disclosure path and same removal condition as :127."
    ),
    # (b) LABELED-SYNTHETIC-SOURCE — beta market-data generators.
    "app/services/ingest.py:64": (
        "_generate_bars: deterministic synthetic OHLCV (seeded random walk from "
        "hardcoded base prices) for the no-provider beta. Output stamped with the "
        "request `source`; the non-'yfinance'/'chain' label is classified "
        "is_synthetic and failed closed by decision_packet_adapter._classify_source "
        "(enforced: test_p0_synthetic_source_failclosed.py)."
    ),
    "app/services/ingest.py:107": (
        "_generate_news: deterministic templated synthetic news for the "
        "no-provider beta. Source-stamped; treated as synthetic evidence and "
        "failed closed downstream via the source allowlist "
        "(enforced: test_p0_synthetic_source_failclosed.py)."
    ),
    # (a) NON-SERVING — never reaches a user.
    "app/services/rl_agents.py:67": (
        "random_valid_agent: shuffles tickers — a constraint-validation test "
        "agent, never a live recommendation path."
    ),
    "app/services/rl_agents.py:72": (
        "random_valid_agent: random weight draw — constraint-validation test "
        "agent only; output never surfaced to users."
    ),
    "app/services/finrlx_research.py:585": (
        "TinyOfflineEnv research training stub: seeds numpy — shadow/research "
        "only, no live influence."
    ),
    "app/services/finrlx_research.py:593": (
        "TinyOfflineEnv research training stub: synthetic observation for an "
        "offline RL smoke-train — shadow/research only, never served."
    ),
}

FICTION_SCAN_BASELINE: frozenset[str] = frozenset(KNOWN_FICTION_SITES)


def classify_fiction(findings: Iterable[FictionFinding]) -> dict[str, list[str]]:
    """Split scan findings into accepted ``debt`` vs ``unclassified`` (new)."""
    locations = {f.location for f in findings}
    return {
        "debt": sorted(locations & FICTION_SCAN_BASELINE),
        "unclassified": sorted(locations - FICTION_SCAN_BASELINE),
    }


if __name__ == "__main__":  # pragma: no cover - operator listing
    import json

    found = scan_fiction_risks()
    print(json.dumps([f.__dict__ for f in found], indent=2))
    split = classify_fiction(found)
    print(f"\n{len(found)} findings — "
          f"debt={len(split['debt'])} unclassified={len(split['unclassified'])}")
