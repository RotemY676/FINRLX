"""Phase 18.2 — SEC 10-K / 10-Q HTML → text extraction.

The SEC publishes filings as iXBRL-tagged HTML, not PDF. Each filing's
primary document (e.g. `nvda-20260126.htm`) is a single HTML file
typically 2–15 MB, containing:

  - The narrative body (Items 1–15 in a 10-K, Items 1–6 in a 10-Q)
    — MD&A, risk factors, business description.
  - Financial-statement tables (income statement, balance sheet,
    cash flows) marked up with iXBRL tags.
  - Lots of boilerplate (cover page, table of contents, signatures,
    XBRL taxonomy noise).

What this module returns: a single normalized-whitespace string of
ALL visible text in the document, with structural tags stripped.
Tables collapse to run-together numbers; that's acceptable for an
LLM analysis prompt where the narrative does the heavy lifting and
the model is good at re-discovering tabular numbers in prose form.

We do NOT try to:
  - Extract clean tables (a real project; iXBRL tags help but parsing
    nested layouts well takes a custom extractor).
  - Detect MD&A vs Risk Factors vs Business sections automatically.
    LLMs handle the unstructured concatenation fine; section
    detection adds fragility for negligible gain.

Two public functions:
  - `fetch_filing_bytes(url)` downloads with SEC-compliant headers
    (User-Agent required, gzip enabled). Separate from parsing so
    tests can stub each layer independently.
  - `extract_text_from_filing(html_bytes)` does the parse + normalize.

Both raise EdgarUpstreamError / EdgarExtractionError respectively so
the orchestrator (Phase 18.4) can translate each into a clear HTTP
status.
"""
from __future__ import annotations

import re

import httpx

from app.core.config import settings
from app.services.edgar.ticker_lookup import (
    EdgarConfigError,
    EdgarUpstreamError,
)


_DOWNLOAD_TIMEOUT_SECONDS = 60.0
# SEC filings can be large — 10-Ks routinely hit 10+ MB. Cap at 50 MB
# to match the PDF upload cap (settings.documents_max_size_mb) so the
# downstream storage tier doesn't see anything bigger via this path
# than it already accepts via the upload path.
_MAX_BYTES = 50 * 1024 * 1024


class EdgarExtractionError(RuntimeError):
    """Raised when filing HTML can't be parsed (truncated, not HTML,
    decode failure). Distinct from upstream errors (download failures)."""


async def fetch_filing_bytes(url: str) -> bytes:
    """Download a filing's primary document from www.sec.gov.

    Enforces:
      - SEC_USER_AGENT must be set (raises EdgarConfigError otherwise).
      - Size cap: response body > _MAX_BYTES is rejected (raises
        EdgarUpstreamError).
      - Status: non-200 raises EdgarUpstreamError.

    Returns the raw response bytes. Decoding is deferred to the
    extractor so BeautifulSoup can autodetect the encoding (filings
    are typically UTF-8 but older ones may be Windows-1252).
    """
    user_agent = (settings.sec_user_agent or "").strip()
    if not user_agent:
        raise EdgarConfigError(
            "SEC_USER_AGENT is empty. SEC requires a User-Agent header "
            "of the form 'AppName operator@example.com' on every "
            "request. Set the env var before calling EDGAR services."
        )
    if not url or not url.strip():
        raise ValueError("url is empty")

    headers = {
        "User-Agent": user_agent,
        # SEC's CDN serves gzip-encoded content; httpx handles
        # decompression transparently when we accept it.
        "Accept-Encoding": "gzip, deflate",
        "Accept": "text/html,application/xhtml+xml",
    }

    try:
        async with httpx.AsyncClient(timeout=_DOWNLOAD_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, headers=headers)
    except httpx.HTTPError as e:
        raise EdgarUpstreamError(
            f"Failed to download SEC filing: {e}"
        ) from e

    if resp.status_code == 404:
        raise EdgarUpstreamError(
            f"SEC returned 404 for filing URL: {url}. The accession may "
            "have been withdrawn, or the primary_doc_name may not match "
            "the file actually present in the Archives index."
        )
    if resp.status_code != 200:
        raise EdgarUpstreamError(
            f"SEC filing download returned status {resp.status_code}."
        )

    content = resp.content
    if len(content) > _MAX_BYTES:
        raise EdgarUpstreamError(
            f"SEC filing exceeds {_MAX_BYTES // (1024 * 1024)} MB cap "
            f"(got {len(content) // (1024 * 1024)} MB). The filing may "
            "include large image exhibits — consider downloading the "
            "narrative-only Form 10-K Document via the SEC viewer."
        )
    return content


# Compiled once: collapses runs of any whitespace (including newlines,
# non-breaking spaces, etc.) into a single ASCII space.
_WHITESPACE_RE = re.compile(r"\s+", flags=re.UNICODE)


def _import_bs4():
    """Lazy import so the rest of the app pays no cost when no
    EDGAR ingest happens (which is most of the time)."""
    try:
        from bs4 import BeautifulSoup  # type: ignore[import-not-found]
    except ImportError as e:
        raise EdgarExtractionError(
            "beautifulsoup4 is not installed. Add `beautifulsoup4` to "
            "backend/requirements.txt and `pip install -r requirements.txt`."
        ) from e
    return BeautifulSoup


def extract_text_from_filing(html_bytes: bytes) -> str:
    """Parse a 10-K/10-Q HTML filing and return a single normalized
    text string.

    Strips:
      - <script>, <style>, <head> tags (and their contents).
      - All other HTML structure (tags become invisible; only text
        nodes survive).
      - Repeated whitespace (collapsed to single spaces).

    Raises EdgarExtractionError when the bytes can't be parsed as
    HTML (e.g. a truncated download, a PDF returned instead of HTML).
    """
    if not html_bytes:
        raise EdgarExtractionError("html_bytes is empty")

    BeautifulSoup = _import_bs4()

    try:
        # BeautifulSoup auto-detects encoding from the byte string.
        # html.parser is stdlib — slower than lxml but adds no native
        # deps. Adequate for one-off filing parses (we don't loop
        # over thousands per request).
        soup = BeautifulSoup(html_bytes, "html.parser")
    except Exception as e:  # bs4 raises a variety of internal exceptions
        raise EdgarExtractionError(f"failed to parse filing HTML: {e}") from e

    # Drop tags whose text content is meaningless to the LLM. The
    # `.decompose()` call removes the tag AND its children, which is
    # what we want here (a <script> tag's text body is JavaScript, not
    # filing content).
    for tag_name in ("script", "style", "head", "noscript"):
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # `get_text(separator=" ")` inserts a single space between every
    # text node so adjacent words don't run together (the default
    # separator is empty, which produces things like "RevenueGrowth").
    raw = soup.get_text(separator=" ")

    # Normalize: collapse all whitespace runs into single ASCII
    # spaces, then trim. SEC filings ship with lots of
    # &nbsp;/U+00A0 and tab indentation that bloat the text without
    # carrying signal.
    normalized = _WHITESPACE_RE.sub(" ", raw).strip()

    if not normalized:
        raise EdgarExtractionError(
            "filing parsed successfully but contained no visible text "
            "(every element was script/style/empty). The download may "
            "be a placeholder rather than the full filing."
        )

    return normalized
