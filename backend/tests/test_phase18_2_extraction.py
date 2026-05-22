"""Phase 18.2 — SEC filing HTML → text extraction contract tests.

Covers both `fetch_filing_bytes` (download with SEC-compliant headers)
and `extract_text_from_filing` (HTML parse + normalize).

What these pin:
  - Download: User-Agent must be set; cap on size; 404/5xx surface as
    EdgarUpstreamError with helpful detail.
  - Extraction: scripts/styles stripped; whitespace normalized; empty
    body raises; truncated / non-HTML still parses gracefully but
    raises only when nothing extractable survives.
  - 10-K/10-Q-shaped fixture round-trips: MD&A narrative comes out
    intact; iXBRL tags stripped; numeric values from a simple table
    appear in the extracted text.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest


# A small but realistic 10-Q-shaped HTML fixture — narrative,
# nested layout, table, script noise, and iXBRL-style tags.
FILING_HTML_FIXTURE = b"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>NVDA 10-Q</title>
  <style>body { font-family: serif; }</style>
  <script>var ix = window.ix || {};</script>
</head>
<body>
  <ix:hidden>iXBRL taxonomy noise</ix:hidden>
  <div class="cover">
    <h1>NVIDIA CORPORATION</h1>
    <h2>FORM 10-Q</h2>
    <p>For the quarterly period ended October 26, 2025</p>
  </div>
  <section id="mdna">
    <h3>Management's Discussion and Analysis</h3>
    <p>Revenue&nbsp;for&nbsp;the&nbsp;quarter&nbsp;was&nbsp;$35.1B,
       up 94% year over year, driven by Data Center growth.</p>
    <p>Gross margin expanded to&#160;75.0%, up 320 bps year over year.</p>
  </section>
  <table>
    <tr><th>Metric</th><th>Q3 FY26</th><th>Q3 FY25</th></tr>
    <tr><td>Revenue</td><td>$35,082</td><td>$18,120</td></tr>
    <tr><td>Operating&nbsp;Income</td><td>$21,869</td><td>$10,417</td></tr>
  </table>
  <script>(function(){ /* page-tracking */ })();</script>
</body>
</html>
"""


# ── extract_text_from_filing ────────────────────────────────────────


def test_extract_strips_script_and_style():
    """Script and style content must NOT appear in the output."""
    from app.services.edgar.extraction import extract_text_from_filing

    text = extract_text_from_filing(FILING_HTML_FIXTURE)

    assert "window.ix" not in text       # script body gone
    assert "font-family" not in text     # style body gone
    assert "page-tracking" not in text   # inline script gone


def test_extract_preserves_narrative_text():
    """MD&A paragraphs come through (whitespace-normalized)."""
    from app.services.edgar.extraction import extract_text_from_filing

    text = extract_text_from_filing(FILING_HTML_FIXTURE)

    assert "NVIDIA CORPORATION" in text
    assert "Management's Discussion and Analysis" in text
    # &nbsp; entities become spaces; the sentence reads naturally.
    assert "Revenue for the quarter was $35.1B" in text
    assert "up 94% year over year" in text
    assert "Gross margin expanded to 75.0%" in text


def test_extract_preserves_table_numeric_content():
    """Tables collapse to run-together text but the numbers survive,
    which is what the LLM needs for cross-quarter comparison."""
    from app.services.edgar.extraction import extract_text_from_filing

    text = extract_text_from_filing(FILING_HTML_FIXTURE)

    assert "$35,082" in text
    assert "$18,120" in text
    assert "Operating Income" in text


def test_extract_normalizes_whitespace():
    """Multiple spaces / tabs / newlines / nbsp collapse to single
    ASCII spaces. No bare \\n, \\t, or U+00A0 in the output."""
    from app.services.edgar.extraction import extract_text_from_filing

    text = extract_text_from_filing(FILING_HTML_FIXTURE)

    assert "\n" not in text
    assert "\t" not in text
    assert " " not in text          # non-breaking space
    assert "  " not in text              # no double spaces


def test_extract_empty_bytes_raises():
    from app.services.edgar.extraction import (
        EdgarExtractionError,
        extract_text_from_filing,
    )

    with pytest.raises(EdgarExtractionError):
        extract_text_from_filing(b"")


def test_extract_all_script_no_visible_text_raises():
    """A filing that parses but contains no visible text is suspicious
    (probably a placeholder) — raise so the caller doesn't persist a
    blank ResearchDocument."""
    from app.services.edgar.extraction import (
        EdgarExtractionError,
        extract_text_from_filing,
    )

    placeholder = b"<html><head></head><body><script>x=1;</script></body></html>"
    with pytest.raises(EdgarExtractionError) as exc_info:
        extract_text_from_filing(placeholder)
    assert "no visible text" in str(exc_info.value).lower()


def test_extract_handles_unclosed_tags_gracefully():
    """Real SEC filings have plenty of malformed HTML. BeautifulSoup's
    html.parser is permissive — we should not crash on it."""
    from app.services.edgar.extraction import extract_text_from_filing

    sloppy = b"<html><body><p>Revenue rose <b>20%</body></html>"
    text = extract_text_from_filing(sloppy)
    assert "Revenue rose" in text
    assert "20%" in text


# ── fetch_filing_bytes ──────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _user_agent_set(monkeypatch):
    from app.core import config as config_mod
    monkeypatch.setattr(
        config_mod.settings, "sec_user_agent", "FINRLX-Test test@example.com"
    )


def _mock_download_response(body: bytes, status_code: int = 200):
    """Patch httpx.AsyncClient.get to return a canned response with
    the given body bytes."""
    async def fake_get(self, url, headers=None):
        response = AsyncMock(spec=httpx.Response)
        response.status_code = status_code
        response.content = body
        return response
    return fake_get


@pytest.mark.asyncio
async def test_fetch_filing_happy_path_returns_bytes():
    from app.services.edgar.extraction import fetch_filing_bytes

    body = b"<html><body>hi</body></html>"
    with patch.object(httpx.AsyncClient, "get", _mock_download_response(body)):
        result = await fetch_filing_bytes(
            "https://www.sec.gov/Archives/edgar/data/1045810/000.../nvda.htm"
        )

    assert result == body


@pytest.mark.asyncio
async def test_fetch_filing_sets_user_agent_header():
    """SEC's fair-access policy: the User-Agent header MUST be sent.
    If we forget it, real production calls will be blocked."""
    from app.services.edgar.extraction import fetch_filing_bytes

    captured = {"headers": None}

    async def capturing_get(self, url, headers=None):
        captured["headers"] = headers
        response = AsyncMock(spec=httpx.Response)
        response.status_code = 200
        response.content = b"<html><body>ok</body></html>"
        return response

    with patch.object(httpx.AsyncClient, "get", capturing_get):
        await fetch_filing_bytes("https://www.sec.gov/Archives/edgar/data/1/x/y.htm")

    assert captured["headers"] is not None
    assert "FINRLX-Test test@example.com" in captured["headers"].get("User-Agent", "")


@pytest.mark.asyncio
async def test_fetch_filing_missing_user_agent_aborts_before_network(monkeypatch):
    from app.core import config as config_mod
    from app.services.edgar import EdgarConfigError
    from app.services.edgar.extraction import fetch_filing_bytes

    monkeypatch.setattr(config_mod.settings, "sec_user_agent", "")

    async def fake_get(self, url, headers=None):
        raise AssertionError("download hit network despite missing UA")

    with patch.object(httpx.AsyncClient, "get", fake_get):
        with pytest.raises(EdgarConfigError):
            await fetch_filing_bytes("https://www.sec.gov/x.htm")


@pytest.mark.asyncio
async def test_fetch_filing_404_raises_upstream_error_with_url():
    from app.services.edgar import EdgarUpstreamError
    from app.services.edgar.extraction import fetch_filing_bytes

    with patch.object(httpx.AsyncClient, "get", _mock_download_response(b"", 404)):
        with pytest.raises(EdgarUpstreamError) as exc_info:
            await fetch_filing_bytes("https://www.sec.gov/missing.htm")

    assert "404" in str(exc_info.value)
    assert "missing.htm" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fetch_filing_non_200_raises_upstream_error():
    from app.services.edgar import EdgarUpstreamError
    from app.services.edgar.extraction import fetch_filing_bytes

    with patch.object(httpx.AsyncClient, "get", _mock_download_response(b"", 503)):
        with pytest.raises(EdgarUpstreamError) as exc_info:
            await fetch_filing_bytes("https://www.sec.gov/x.htm")

    assert "503" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fetch_filing_network_error_raises_upstream_error():
    from app.services.edgar import EdgarUpstreamError
    from app.services.edgar.extraction import fetch_filing_bytes

    async def fake_get(self, url, headers=None):
        raise httpx.ConnectError("DNS failure")

    with patch.object(httpx.AsyncClient, "get", fake_get):
        with pytest.raises(EdgarUpstreamError):
            await fetch_filing_bytes("https://www.sec.gov/x.htm")


@pytest.mark.asyncio
async def test_fetch_filing_oversize_raises_upstream_error():
    """A 60 MB filing exceeds the 50 MB cap and must be rejected
    before we accept the bytes into memory for parsing."""
    from app.services.edgar import EdgarUpstreamError
    from app.services.edgar.extraction import fetch_filing_bytes

    too_big = b"x" * (51 * 1024 * 1024)
    with patch.object(httpx.AsyncClient, "get", _mock_download_response(too_big)):
        with pytest.raises(EdgarUpstreamError) as exc_info:
            await fetch_filing_bytes("https://www.sec.gov/big.htm")

    assert "cap" in str(exc_info.value).lower() or "MB" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fetch_filing_empty_url_raises_value_error():
    from app.services.edgar.extraction import fetch_filing_bytes

    with pytest.raises(ValueError):
        await fetch_filing_bytes("")


# ── End-to-end on the fixture ───────────────────────────────────────


@pytest.mark.asyncio
async def test_download_then_extract_round_trip():
    """The two public functions compose: download bytes, extract text."""
    from app.services.edgar.extraction import (
        extract_text_from_filing,
        fetch_filing_bytes,
    )

    with patch.object(
        httpx.AsyncClient, "get", _mock_download_response(FILING_HTML_FIXTURE)
    ):
        body = await fetch_filing_bytes("https://www.sec.gov/Archives/.../nvda.htm")

    text = extract_text_from_filing(body)
    assert "NVIDIA CORPORATION" in text
    assert "$35,082" in text
