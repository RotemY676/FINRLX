"""LEAP A1 — SEC XBRL `companyfacts` client (decision D43/D51).

Free, official, keyless fundamentals from data.sec.gov:
  - ticker -> CIK via the SEC's company_tickers.json (cached in-process)
  - companyfacts -> annual (10-K) ratio TRENDS the Analyst Desk renders:
      revenue, net_income, net_margin, leverage (liabilities/equity),
      shares outstanding + YoY dilution

Etiquette (D51): every request carries a descriptive User-Agent with a
contact (SEC fair-access policy), and results are cached aggressively
(in-process TTL) so a dossier build costs at most two upstream hits.

Honesty: any missing concept degrades to None for that metric; a ticker
without a CIK or without usable facts returns available=False with the
reason — sections never fabricate.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:0>10}.json"
_CACHE_TTL_S = 6 * 3600
MAX_YEARS = 5

# us-gaap concept fallback chains (filers vary)
REVENUE_TAGS = (
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "SalesRevenueNet",
)
NET_INCOME_TAGS = ("NetIncomeLoss", "ProfitLoss")
LIABILITIES_TAGS = ("Liabilities",)
EQUITY_TAGS = (
    "StockholdersEquity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
)
SHARES_TAGS_DEI = ("EntityCommonStockSharesOutstanding",)
SHARES_TAGS_GAAP = ("CommonStockSharesOutstanding",)

_lock = threading.Lock()
_ticker_map: dict[str, int] | None = None
_ticker_map_at = 0.0
_facts_cache: dict[int, tuple[float, dict]] = {}


def _user_agent() -> str:
    contact = os.environ.get("SEC_CONTACT_EMAIL", "ops@finrlx.example")
    return f"FINRLX research desk ({contact})"


def _get(url: str) -> dict | None:
    try:
        resp = httpx.get(url, headers={"User-Agent": _user_agent()}, timeout=20.0)
        if resp.status_code != 200:
            logger.warning("SEC %s -> %s", url, resp.status_code)
            return None
        return resp.json()
    except Exception as exc:  # noqa: BLE001 — provider boundary
        logger.warning("SEC fetch failed %s: %s", url, exc)
        return None


def resolve_cik(ticker: str) -> int | None:
    global _ticker_map, _ticker_map_at
    with _lock:
        stale = _ticker_map is None or (time.time() - _ticker_map_at) > _CACHE_TTL_S
    if stale:
        data = _get(SEC_TICKERS_URL)
        if data:
            mapping = {
                str(row.get("ticker", "")).upper(): int(row.get("cik_str", 0))
                for row in data.values()
                if isinstance(row, dict)
            }
            with _lock:
                _ticker_map, _ticker_map_at = mapping, time.time()
    with _lock:
        return (_ticker_map or {}).get(ticker.upper())


def _fetch_facts(cik: int) -> dict | None:
    with _lock:
        hit = _facts_cache.get(cik)
        if hit and (time.time() - hit[0]) < _CACHE_TTL_S:
            return hit[1]
    data = _get(SEC_FACTS_URL.format(cik=cik))
    if data is not None:
        with _lock:
            _facts_cache[cik] = (time.time(), data)
    return data


def _annual_series(facts: dict, taxonomy: str, tags: tuple[str, ...]) -> list[dict]:
    """FY (10-K) values for the first tag with usable data: [{fy, end, value}]."""
    node = facts.get("facts", {}).get(taxonomy, {})
    for tag in tags:
        units = (node.get(tag) or {}).get("units") or {}
        # prefer USD / shares unit keys
        for unit_key in ("USD", "shares", *units.keys()):
            rows = units.get(unit_key)
            if not rows:
                continue
            annual: dict[int, dict] = {}
            for r in rows:
                if r.get("form") != "10-K" or r.get("fp") != "FY":
                    continue
                fy = r.get("fy")
                if not isinstance(fy, int):
                    continue
                # keep the latest-filed value per fiscal year
                prev = annual.get(fy)
                if prev is None or str(r.get("filed", "")) > str(prev.get("filed", "")):
                    annual[fy] = r
            if annual:
                out = [
                    {"fy": fy, "end": r.get("end"), "value": r.get("val")}
                    for fy, r in sorted(annual.items())
                ]
                return out[-MAX_YEARS:]
    return []


def _ratio(a: float | None, b: float | None) -> float | None:
    if a is None or b in (None, 0):
        return None
    return round(a / b, 4)


def build_xbrl_trends(ticker: str) -> dict:
    """The `fundamentals.xbrl` payload for the dossier/desk."""
    cik = resolve_cik(ticker)
    if cik is None:
        return {"available": False, "reason": "no_sec_cik", "source": "sec_xbrl"}
    facts = _fetch_facts(cik)
    if not facts:
        return {"available": False, "reason": "sec_unreachable", "source": "sec_xbrl"}

    revenue = _annual_series(facts, "us-gaap", REVENUE_TAGS)
    net_income = _annual_series(facts, "us-gaap", NET_INCOME_TAGS)
    liabilities = _annual_series(facts, "us-gaap", LIABILITIES_TAGS)
    equity = _annual_series(facts, "us-gaap", EQUITY_TAGS)
    shares = _annual_series(facts, "dei", SHARES_TAGS_DEI) or _annual_series(
        facts, "us-gaap", SHARES_TAGS_GAAP
    )

    by_fy = lambda series: {row["fy"]: row["value"] for row in series}  # noqa: E731
    rev_by, ni_by = by_fy(revenue), by_fy(net_income)
    li_by, eq_by, sh_by = by_fy(liabilities), by_fy(equity), by_fy(shares)

    years = sorted(set(rev_by) | set(ni_by))[-MAX_YEARS:]
    margins = [
        {"fy": y, "value": _ratio(ni_by.get(y), rev_by.get(y))} for y in years
    ]
    lev_years = sorted(set(li_by) & set(eq_by))[-MAX_YEARS:]
    leverage = [
        {"fy": y, "value": _ratio(li_by.get(y), eq_by.get(y))} for y in lev_years
    ]
    sh_years = sorted(sh_by)[-MAX_YEARS:]
    dilution = []
    for prev, cur in zip(sh_years, sh_years[1:]):
        if sh_by.get(prev):
            dilution.append(
                {"fy": cur, "value": round(sh_by[cur] / sh_by[prev] - 1.0, 4)}
            )

    available = bool(revenue or net_income)
    return {
        "available": available,
        "source": "sec_xbrl",
        "entity": facts.get("entityName"),
        "cik": cik,
        "revenue": revenue,
        "net_income": net_income,
        "net_margin": margins,
        "leverage_liab_over_equity": leverage,
        "shares_outstanding": shares,
        "dilution_yoy": dilution,
        "note": (
            None
            if available
            else "SEC XBRL has no usable annual revenue/income facts for this filer."
        ),
    }
