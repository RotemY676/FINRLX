"""Phase 18.1 — SEC EDGAR filings fetcher.

Given a CIK (from Phase 18.0's `resolve_ticker`), returns the most
recent quarterly filings (10-Q / 10-K), most recent first. The
returned `EdgarFiling` records carry enough metadata for Phase 18.2
to download the primary document and Phase 18.3 to persist a
`ResearchDocument` row keyed on the accession number.

Data source: https://data.sec.gov/submissions/CIK{cik}.json — the
authoritative SEC endpoint. Shape (only the fields we read):

    {
      "cik": "0001045810",
      "entityName": "NVIDIA CORP",
      "filings": {
        "recent": {
          "accessionNumber": ["0001045810-26-000012", ...],
          "filingDate":      ["2026-02-21", ...],
          "reportDate":      ["2026-01-26", ...],
          "form":            ["10-K", "10-Q", "8-K", ...],
          "primaryDocument": ["nvda-20260126.htm", ...]
        },
        "files": [ ... older paginated chunks ... ]
      }
    }

The "recent" block holds the ~1000 most recent filings as parallel
arrays sorted most-recent-first. For 6 quarterly filings (~18 months
back) we never need to walk into "files" — this is the design point
that keeps 18.1 to a single SEC request.

Form scope: this phase accepts ONLY the unamended originals "10-K"
and "10-Q". Amendments ("10-K/A", "10-Q/A") are skipped because they
typically correct specific items rather than restate the full filing;
treating them as separate quarters would double-count. Foreign-issuer
forms (20-F, 6-K) are out of scope — Phase 18 ships US-coverage only.

URL construction (filings.SEC.gov requires this exact format):

    https://www.sec.gov/Archives/edgar/data/{cik_unpadded}/{accession_no_no_dashes}/{primaryDocument}

The CIK in the URL path is UNPADDED (leading zeros stripped), but the
data API requires the PADDED form — easy to get wrong, which is why
both are computed explicitly from a single input.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import httpx

from app.core.config import settings
from app.services.edgar.ticker_lookup import (
    EdgarConfigError,
    EdgarUpstreamError,
)


_SUBMISSIONS_URL_TMPL = "https://data.sec.gov/submissions/CIK{cik}.json"
_REQUEST_TIMEOUT_SECONDS = 30.0
_QUARTERLY_FORMS = frozenset({"10-Q", "10-K"})
_DEFAULT_FILING_LIMIT = 6


@dataclass(frozen=True)
class EdgarFiling:
    """A single quarterly filing as exposed by SEC EDGAR.

    `period_of_report` is the more useful "which quarter" indicator
    (e.g. 2025-10-26 = NVIDIA's Q3 FY26). `filing_date` is when the
    document was submitted to SEC and is what we sort by — the same
    period can be re-filed (rare) or amended."""
    accession_no: str          # "0001045810-26-000012"
    form: str                  # "10-K" or "10-Q"
    filing_date: date          # date SEC received the filing
    period_of_report: date     # reporting period end
    primary_doc_name: str      # e.g. "nvda-20260126.htm"
    primary_doc_url: str       # full https URL to the .htm document


def _build_primary_doc_url(cik_padded: str, accession_no: str, doc_name: str) -> str:
    """Compose the absolute URL to a filing's primary document.

    Two gotchas the SEC docs gloss over:
      1. The {cik} segment is UNPADDED in the Archives URL (despite
         being padded in the data.sec.gov URL).
      2. The accession number's dashes are removed for the URL
         segment (but kept in the JSON field).
    """
    cik_unpadded = str(int(cik_padded))  # "0001045810" → "1045810"
    accession_path = accession_no.replace("-", "")  # "0001...-26-000012" → "00010...26000012"
    return (
        f"https://www.sec.gov/Archives/edgar/data/"
        f"{cik_unpadded}/{accession_path}/{doc_name}"
    )


def _safe_parse_date(value: str | None) -> date | None:
    """SEC date strings are ISO 'YYYY-MM-DD'. Empty / malformed
    values are tolerated (some non-periodic filings like 8-K have an
    empty reportDate)."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


async def fetch_recent_quarterly_filings(
    cik: str,
    *,
    limit: int = _DEFAULT_FILING_LIMIT,
) -> list[EdgarFiling]:
    """Return up to `limit` most-recent quarterly filings (10-K, 10-Q)
    for the given CIK, most recent first.

    Args:
      cik: 10-digit zero-padded CIK string (as returned by
        `resolve_ticker`). Accepts unpadded too — we pad defensively.
      limit: max number of filings to return (default 6).

    Raises:
      - EdgarConfigError: SEC_USER_AGENT is empty.
      - EdgarUpstreamError: SEC unreachable, non-200, malformed JSON,
        or CIK has no submissions record (404).
      - ValueError: cik is empty / not a number.

    Returns:
      List of EdgarFiling, possibly empty if the company has filed
      neither 10-K nor 10-Q (e.g. a recently registered shell).
    """
    user_agent = (settings.sec_user_agent or "").strip()
    if not user_agent:
        raise EdgarConfigError(
            "SEC_USER_AGENT is empty. SEC requires a User-Agent header "
            "of the form 'AppName operator@example.com' on every "
            "request. Set the env var before calling EDGAR services."
        )
    if not cik or not cik.strip():
        raise ValueError("cik is empty")
    cik_clean = cik.strip()
    if not cik_clean.isdigit():
        raise ValueError(f"cik must be all digits, got {cik_clean!r}")

    cik_padded = cik_clean.zfill(10)
    url = _SUBMISSIONS_URL_TMPL.format(cik=cik_padded)
    headers = {
        "User-Agent": user_agent,
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, headers=headers)
    except httpx.HTTPError as e:
        raise EdgarUpstreamError(
            f"Failed to reach SEC submissions endpoint: {e}"
        ) from e

    if resp.status_code == 404:
        # CIK doesn't exist or was deregistered. Distinct from a
        # missing User-Agent (which 403s) — surface a useful hint.
        raise EdgarUpstreamError(
            f"SEC has no submissions record for CIK {cik_padded}. "
            "The company may have been deregistered, the CIK may be "
            "wrong, or it may be too newly registered to appear yet."
        )
    if resp.status_code != 200:
        raise EdgarUpstreamError(
            f"SEC submissions endpoint returned status {resp.status_code}. "
            "If this is 403, verify SEC_USER_AGENT contains a real "
            "contact email."
        )

    try:
        payload = resp.json()
    except ValueError as e:
        raise EdgarUpstreamError(
            "SEC submissions endpoint returned non-JSON body."
        ) from e

    if not isinstance(payload, dict):
        raise EdgarUpstreamError(
            f"SEC submissions payload has unexpected shape: {type(payload).__name__}"
        )

    recent = payload.get("filings", {}).get("recent", {}) if isinstance(payload.get("filings"), dict) else {}
    if not isinstance(recent, dict):
        return []

    accession_nos = recent.get("accessionNumber") or []
    forms = recent.get("form") or []
    filing_dates = recent.get("filingDate") or []
    report_dates = recent.get("reportDate") or []
    primary_docs = recent.get("primaryDocument") or []

    # SEC publishes these as parallel arrays of equal length. We
    # iterate by the shortest length defensively — a mismatch would
    # be a SEC bug, but a defensive bound prevents a crash that
    # blocks the whole ingest.
    n = min(
        len(accession_nos), len(forms),
        len(filing_dates), len(primary_docs),
    )

    results: list[EdgarFiling] = []
    for i in range(n):
        form = forms[i]
        if form not in _QUARTERLY_FORMS:
            continue
        accession_no = accession_nos[i]
        primary_doc = primary_docs[i]
        filing_date = _safe_parse_date(filing_dates[i])
        if not (accession_no and primary_doc and filing_date):
            continue

        # reportDate is parallel but can be empty for non-periodic
        # forms; 10-K/10-Q always have it, but stay defensive.
        report_date_str = report_dates[i] if i < len(report_dates) else None
        period_of_report = _safe_parse_date(report_date_str) or filing_date

        results.append(EdgarFiling(
            accession_no=accession_no,
            form=form,
            filing_date=filing_date,
            period_of_report=period_of_report,
            primary_doc_name=primary_doc,
            primary_doc_url=_build_primary_doc_url(cik_padded, accession_no, primary_doc),
        ))
        if len(results) >= limit:
            break

    # SEC's "recent" block is already sorted newest-first, but sort
    # defensively in case that ordering ever changes.
    results.sort(key=lambda f: f.filing_date, reverse=True)
    return results
