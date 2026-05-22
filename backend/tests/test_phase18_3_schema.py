"""Phase 18.3 — research_documents schema extension contract tests.

What these pin:
  - New columns are nullable except `source` (which defaults to
    'upload' so existing rows backfill cleanly).
  - storage_path is now nullable; sec_auto rows persist without a
    local file.
  - The (ticker, sec_accession_no) unique index dedupes sec_auto rows
    by accession but allows multiple uploads per ticker (NULL ≠ NULL).
  - Same accession under DIFFERENT tickers is allowed (cross-ticker
    re-listings, ETF sub-filings, etc.).
"""
from __future__ import annotations

import secrets
from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.document import ResearchDocument


def _new_row(**overrides) -> ResearchDocument:
    """Build a minimal ResearchDocument with sane defaults; override
    any field for a specific test."""
    defaults = dict(
        ticker="NVDA",
        filename="nvda-10q.htm",
        storage_path=None,           # sec_auto default — no local file
        mime_type="text/html",
        file_size_bytes=0,
        extracted_text="Revenue was $35B.",
        extraction_status="ready",
        uploaded_by_email="auto@finrlx.local",
        source="sec_auto",
        sec_accession_no="0001045810-26-000012",
        sec_form="10-K",
        sec_period_of_report=date(2026, 1, 26),
        external_url="https://www.sec.gov/Archives/edgar/data/1045810/.../nvda.htm",
    )
    defaults.update(overrides)
    return ResearchDocument(**defaults)


@pytest.mark.asyncio
async def test_sec_auto_row_persists_without_storage_path():
    """sec_auto rows insert successfully with storage_path NULL —
    the Phase 18.3 schema change that allowed it."""
    from tests.conftest import test_session_factory

    accession = f"acc-{secrets.token_hex(4)}"
    async with test_session_factory() as db:
        row = _new_row(sec_accession_no=accession)
        db.add(row)
        await db.commit()
        saved = (
            await db.execute(select(ResearchDocument).where(ResearchDocument.id == row.id))
        ).scalar_one()

    assert saved.storage_path is None
    assert saved.source == "sec_auto"
    assert saved.sec_accession_no == accession
    assert saved.sec_form == "10-K"
    assert saved.sec_period_of_report == date(2026, 1, 26)
    assert saved.external_url is not None


@pytest.mark.asyncio
async def test_source_defaults_to_upload_when_omitted():
    """An insert that omits `source` (e.g. existing Phase 17 upload
    code path) gets 'upload' via the server default."""
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        row = ResearchDocument(
            ticker="MSFT",
            filename="msft.pdf",
            storage_path="MSFT/abc.pdf",
            mime_type="application/pdf",
            file_size_bytes=1024,
            extraction_status="ready",
            uploaded_by_email="op@example.com",
        )
        db.add(row)
        await db.commit()
        saved = (
            await db.execute(select(ResearchDocument).where(ResearchDocument.id == row.id))
        ).scalar_one()

    assert saved.source == "upload"
    assert saved.sec_accession_no is None
    assert saved.sec_form is None


@pytest.mark.asyncio
async def test_duplicate_sec_accession_same_ticker_raises():
    """Re-ingesting the same SEC filing (same ticker + accession) must
    fail at the DB level — that's how 18.4's orchestrator stays
    idempotent."""
    from tests.conftest import test_session_factory

    accession = f"acc-{secrets.token_hex(4)}"
    async with test_session_factory() as db:
        db.add(_new_row(ticker="GOOG", sec_accession_no=accession))
        await db.commit()

    async with test_session_factory() as db:
        db.add(_new_row(ticker="GOOG", sec_accession_no=accession))
        with pytest.raises(IntegrityError):
            await db.commit()


@pytest.mark.asyncio
async def test_same_accession_different_ticker_allowed():
    """A registered filing tied to two tickers (rare but legal —
    cross-listings, ETF underlying sub-filings) is allowed. The
    dedup constraint is composite, not on accession alone."""
    from tests.conftest import test_session_factory

    accession = f"acc-{secrets.token_hex(4)}"
    async with test_session_factory() as db:
        db.add(_new_row(ticker="AAPL", sec_accession_no=accession))
        db.add(_new_row(ticker="MSFT", sec_accession_no=accession))
        await db.commit()  # should not raise

    async with test_session_factory() as db:
        rows = (
            await db.execute(
                select(ResearchDocument).where(ResearchDocument.sec_accession_no == accession)
            )
        ).scalars().all()
    assert len(rows) == 2


@pytest.mark.asyncio
async def test_multiple_uploads_per_ticker_allowed_when_accession_null():
    """The unique constraint must NOT block two operator uploads for
    the same ticker (both have sec_accession_no NULL). NULL != NULL
    in composite unique constraints."""
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        db.add(
            ResearchDocument(
                ticker="TSLA",
                filename="tsla-q1.pdf",
                storage_path="TSLA/a.pdf",
                mime_type="application/pdf",
                file_size_bytes=1024,
                extraction_status="ready",
                uploaded_by_email="op@example.com",
                source="upload",
            )
        )
        db.add(
            ResearchDocument(
                ticker="TSLA",
                filename="tsla-q2.pdf",
                storage_path="TSLA/b.pdf",
                mime_type="application/pdf",
                file_size_bytes=2048,
                extraction_status="ready",
                uploaded_by_email="op@example.com",
                source="upload",
            )
        )
        await db.commit()  # must not raise

    async with test_session_factory() as db:
        rows = (
            await db.execute(select(ResearchDocument).where(ResearchDocument.ticker == "TSLA"))
        ).scalars().all()
    assert len(rows) >= 2
    # Confirm both have NULL accession (proving the NULL-distinct path).
    assert all(r.sec_accession_no is None for r in rows)
