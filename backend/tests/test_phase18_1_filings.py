"""Phase 18.1 — EDGAR filings fetcher contract tests.

What these pin:
  - Happy path: mixed forms (10-K, 10-Q, 8-K, S-1) → only 10-K/10-Q
    survive, in most-recent-first order, capped at `limit`.
  - URL construction: CIK unpadded in path, accession dashes removed.
  - Padding: caller can pass unpadded CIK ("1045810") and we still
    hit the padded SEC URL ("CIK0001045810.json").
  - Form filter: 10-K/A and 10-Q/A amendments are SKIPPED.
  - period_of_report falls back to filing_date when reportDate is empty.
  - Mismatched array lengths in the "recent" block don't crash.
  - Fewer than `limit` matching forms → returns what's there.
  - SEC_USER_AGENT empty → EdgarConfigError before network.
  - 404 (unknown CIK) → EdgarUpstreamError with helpful detail.
  - Non-200 / network error / malformed JSON → EdgarUpstreamError.
  - Empty / non-digit CIK → ValueError.
"""
from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, patch

import httpx
import pytest


# Realistic SEC submissions fixture — NVIDIA-shaped, abbreviated to
# the fields the fetcher actually reads. Mixed forms test the filter.
SUBMISSIONS_NVDA = {
    "cik": "0001045810",
    "entityName": "NVIDIA CORP",
    "tickers": ["NVDA"],
    "filings": {
        "recent": {
            "accessionNumber": [
                "0001045810-26-000012",  # 10-K
                "0001045810-25-000050",  # 8-K (filter out)
                "0001045810-25-000045",  # 10-Q
                "0001045810-25-000040",  # 10-Q/A (amendment — filter out)
                "0001045810-25-000038",  # S-1 (filter out)
                "0001045810-25-000031",  # 10-Q
                "0001045810-25-000020",  # 10-Q
                "0001045810-25-000010",  # 10-K
                "0001045810-24-000050",  # 10-Q
                "0001045810-24-000045",  # 10-Q (this would be #7, dropped by limit=6)
            ],
            "filingDate": [
                "2026-02-21",
                "2025-12-05",
                "2025-11-19",
                "2025-11-10",
                "2025-10-15",
                "2025-08-27",
                "2025-05-28",
                "2025-02-26",
                "2024-11-20",
                "2024-08-28",
            ],
            "reportDate": [
                "2026-01-26",
                "",                # 8-K has no reportDate
                "2025-10-26",
                "2025-10-26",
                "",                # S-1 has no reportDate
                "2025-07-27",
                "2025-04-27",
                "2025-01-26",
                "2024-10-27",
                "2024-07-28",
            ],
            "form": [
                "10-K", "8-K", "10-Q", "10-Q/A", "S-1",
                "10-Q", "10-Q", "10-K", "10-Q", "10-Q",
            ],
            "primaryDocument": [
                "nvda-20260126.htm",
                "nvda-8k-20251205.htm",
                "nvda-20251026.htm",
                "nvda-20251026-a.htm",
                "nvda-s1.htm",
                "nvda-20250727.htm",
                "nvda-20250427.htm",
                "nvda-20250126.htm",
                "nvda-20241027.htm",
                "nvda-20240728.htm",
            ],
        },
        "files": [],
    },
}


def _mock_sec_response(payload, status_code: int = 200):
    """Patch httpx.AsyncClient.get to return a single canned response."""
    async def fake_get(self, url, headers=None):
        response = AsyncMock(spec=httpx.Response)
        response.status_code = status_code
        response.json = lambda: payload
        return response
    return fake_get


@pytest.fixture(autouse=True)
def _user_agent_set(monkeypatch):
    """Every test gets a valid UA except those that explicitly clear it."""
    from app.core import config as config_mod
    monkeypatch.setattr(
        config_mod.settings, "sec_user_agent", "FINRLX-Test test@example.com"
    )


# ── Happy path ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_returns_only_quarterly_forms_most_recent_first():
    """8-K, S-1, 10-Q/A are filtered out. Result is sorted by
    filing_date descending and capped at the default limit of 6."""
    from app.services.edgar.filings import fetch_recent_quarterly_filings

    with patch.object(httpx.AsyncClient, "get", _mock_sec_response(SUBMISSIONS_NVDA)):
        filings = await fetch_recent_quarterly_filings("0001045810")

    assert len(filings) == 6
    # Most recent first
    assert filings[0].form == "10-K"
    assert filings[0].filing_date == date(2026, 2, 21)
    assert filings[0].period_of_report == date(2026, 1, 26)
    assert filings[0].accession_no == "0001045810-26-000012"

    # All forms are 10-K or 10-Q; no 8-K, S-1, or 10-Q/A
    forms_returned = [f.form for f in filings]
    assert set(forms_returned).issubset({"10-K", "10-Q"})
    assert "10-Q/A" not in forms_returned

    # Verify the ordering is strictly newest-first
    for prev, curr in zip(filings, filings[1:]):
        assert prev.filing_date >= curr.filing_date


@pytest.mark.asyncio
async def test_primary_doc_url_uses_unpadded_cik_and_dashless_accession():
    """URL must be:
    https://www.sec.gov/Archives/edgar/data/1045810/000104581026000012/nvda-20260126.htm
    (CIK unpadded, accession with dashes removed)."""
    from app.services.edgar.filings import fetch_recent_quarterly_filings

    with patch.object(httpx.AsyncClient, "get", _mock_sec_response(SUBMISSIONS_NVDA)):
        filings = await fetch_recent_quarterly_filings("0001045810", limit=1)

    expected = (
        "https://www.sec.gov/Archives/edgar/data/"
        "1045810/000104581026000012/nvda-20260126.htm"
    )
    assert filings[0].primary_doc_url == expected
    assert filings[0].primary_doc_name == "nvda-20260126.htm"


@pytest.mark.asyncio
async def test_unpadded_cik_input_is_padded_for_request():
    """Caller can pass an unpadded CIK; the URL we hit must be the
    padded form (SEC's submissions endpoint requires 10 digits)."""
    from app.services.edgar.filings import fetch_recent_quarterly_filings

    captured = {"url": None}

    async def capturing_get(self, url, headers=None):
        captured["url"] = url
        response = AsyncMock(spec=httpx.Response)
        response.status_code = 200
        response.json = lambda: SUBMISSIONS_NVDA
        return response

    with patch.object(httpx.AsyncClient, "get", capturing_get):
        await fetch_recent_quarterly_filings("1045810", limit=1)

    assert captured["url"] == "https://data.sec.gov/submissions/CIK0001045810.json"


@pytest.mark.asyncio
async def test_limit_parameter_caps_result_count():
    from app.services.edgar.filings import fetch_recent_quarterly_filings

    with patch.object(httpx.AsyncClient, "get", _mock_sec_response(SUBMISSIONS_NVDA)):
        filings = await fetch_recent_quarterly_filings("0001045810", limit=3)
    assert len(filings) == 3
    assert filings[0].accession_no == "0001045810-26-000012"  # newest still wins


@pytest.mark.asyncio
async def test_fewer_than_limit_returns_what_exists():
    """A company with only 2 quarterly filings on record returns 2,
    not an error or padded list."""
    from app.services.edgar.filings import fetch_recent_quarterly_filings

    sparse = {
        "filings": {
            "recent": {
                "accessionNumber": ["acc-1", "acc-2", "acc-3"],
                "filingDate": ["2025-08-01", "2025-05-01", "2025-04-01"],
                "reportDate": ["2025-06-30", "2025-03-31", ""],
                "form": ["10-Q", "10-Q", "8-K"],
                "primaryDocument": ["q1.htm", "q2.htm", "8k.htm"],
            }
        }
    }
    with patch.object(httpx.AsyncClient, "get", _mock_sec_response(sparse)):
        filings = await fetch_recent_quarterly_filings("1234567", limit=6)
    assert len(filings) == 2


@pytest.mark.asyncio
async def test_period_of_report_falls_back_to_filing_date_when_empty():
    """A quarterly filing missing reportDate (shouldn't happen in
    practice, but stay safe) falls back to filing_date."""
    from app.services.edgar.filings import fetch_recent_quarterly_filings

    sparse = {
        "filings": {
            "recent": {
                "accessionNumber": ["acc-1"],
                "filingDate": ["2025-08-01"],
                "reportDate": [""],  # empty
                "form": ["10-Q"],
                "primaryDocument": ["q1.htm"],
            }
        }
    }
    with patch.object(httpx.AsyncClient, "get", _mock_sec_response(sparse)):
        filings = await fetch_recent_quarterly_filings("1234567", limit=1)
    assert filings[0].period_of_report == date(2025, 8, 1)


@pytest.mark.asyncio
async def test_mismatched_array_lengths_do_not_crash():
    """A SEC bug that returned uneven parallel arrays must NOT take
    down the whole ingest. We iterate up to the shortest length."""
    from app.services.edgar.filings import fetch_recent_quarterly_filings

    broken = {
        "filings": {
            "recent": {
                "accessionNumber": ["acc-1", "acc-2"],
                "filingDate": ["2025-08-01"],          # only 1
                "reportDate": ["2025-06-30", "2025-03-31"],
                "form": ["10-Q", "10-Q"],
                "primaryDocument": ["q1.htm", "q2.htm"],
            }
        }
    }
    with patch.object(httpx.AsyncClient, "get", _mock_sec_response(broken)):
        filings = await fetch_recent_quarterly_filings("1234567", limit=6)
    # Only the first row has all parallel fields present, so only 1 returned
    assert len(filings) == 1


@pytest.mark.asyncio
async def test_empty_recent_block_returns_empty_list():
    from app.services.edgar.filings import fetch_recent_quarterly_filings

    empty = {"filings": {"recent": {}}}
    with patch.object(httpx.AsyncClient, "get", _mock_sec_response(empty)):
        filings = await fetch_recent_quarterly_filings("1234567")
    assert filings == []


# ── Error paths ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_missing_user_agent_aborts_before_network(monkeypatch):
    from app.core import config as config_mod
    from app.services.edgar import EdgarConfigError
    from app.services.edgar.filings import fetch_recent_quarterly_filings

    monkeypatch.setattr(config_mod.settings, "sec_user_agent", "")

    async def fake_get(self, url, headers=None):
        raise AssertionError("network call must not happen without UA")

    with patch.object(httpx.AsyncClient, "get", fake_get):
        with pytest.raises(EdgarConfigError):
            await fetch_recent_quarterly_filings("0001045810")


@pytest.mark.asyncio
async def test_404_raises_upstream_error_with_dereg_hint():
    from app.services.edgar import EdgarUpstreamError
    from app.services.edgar.filings import fetch_recent_quarterly_filings

    with patch.object(httpx.AsyncClient, "get", _mock_sec_response({}, status_code=404)):
        with pytest.raises(EdgarUpstreamError) as exc_info:
            await fetch_recent_quarterly_filings("9999999")
    assert "no submissions record" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_403_raises_upstream_error_with_ua_hint():
    from app.services.edgar import EdgarUpstreamError
    from app.services.edgar.filings import fetch_recent_quarterly_filings

    with patch.object(httpx.AsyncClient, "get", _mock_sec_response({}, status_code=403)):
        with pytest.raises(EdgarUpstreamError) as exc_info:
            await fetch_recent_quarterly_filings("0001045810")
    assert "403" in str(exc_info.value)


@pytest.mark.asyncio
async def test_network_error_raises_upstream_error():
    from app.services.edgar import EdgarUpstreamError
    from app.services.edgar.filings import fetch_recent_quarterly_filings

    async def fake_get(self, url, headers=None):
        raise httpx.ConnectError("DNS failure")

    with patch.object(httpx.AsyncClient, "get", fake_get):
        with pytest.raises(EdgarUpstreamError) as exc_info:
            await fetch_recent_quarterly_filings("0001045810")
    assert "Failed to reach SEC" in str(exc_info.value)


@pytest.mark.asyncio
async def test_malformed_payload_raises_upstream_error():
    from app.services.edgar import EdgarUpstreamError
    from app.services.edgar.filings import fetch_recent_quarterly_filings

    with patch.object(httpx.AsyncClient, "get", _mock_sec_response(["not", "a", "dict"])):
        with pytest.raises(EdgarUpstreamError):
            await fetch_recent_quarterly_filings("0001045810")


@pytest.mark.asyncio
async def test_empty_cik_raises_value_error():
    from app.services.edgar.filings import fetch_recent_quarterly_filings

    with pytest.raises(ValueError):
        await fetch_recent_quarterly_filings("")
    with pytest.raises(ValueError):
        await fetch_recent_quarterly_filings("   ")


@pytest.mark.asyncio
async def test_non_digit_cik_raises_value_error():
    from app.services.edgar.filings import fetch_recent_quarterly_filings

    with pytest.raises(ValueError):
        await fetch_recent_quarterly_filings("NVDA")  # ticker, not CIK
