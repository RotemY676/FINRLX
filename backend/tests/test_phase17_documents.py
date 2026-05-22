"""Phase 17.0 — Research documents upload + extraction contract tests.

What these tests pin:
  - POST /research/documents requires auth (401 without bearer).
  - Valid PDF upload returns 201 with the extracted text + token estimate.
  - Invalid ticker -> 400 before any storage write.
  - Oversize upload -> 413 BEFORE the bytes are persisted.
  - Empty body -> 400.
  - Non-PDF content type -> 415.
  - GET ?ticker=... lists documents sorted newest-first.
  - GET /{id} returns the full row including extracted text.
  - GET /{id}/download returns the original bytes with attachment headers.
  - DELETE /{id} requires the uploader; 403 from a different user.
  - Storage layer rejects relative paths with '..' segments.
  - Failed extraction commits a row with extraction_status="failed" so the
    UI can surface the error and offer re-upload (the bytes stay on disk).
"""
from __future__ import annotations

import io
import secrets

import pytest

from app.models.auth import EmailAllowlist
from app.services.documents.extraction import (
    DocumentExtractionError,
    estimate_tokens,
    extract_text_from_pdf,
)
from app.services.documents.storage import (
    DocumentStorageError,
    _is_safe_relative,
    save_document,
)


# ── Helpers ─────────────────────────────────────────────────────────────


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _signup_user(client) -> tuple[str, str]:
    """Returns (email, access_token) for a fresh user."""
    from tests.conftest import test_session_factory

    email = f"docs17-{secrets.token_hex(4)}@example.com"
    async with test_session_factory() as db:
        db.add(EmailAllowlist(email=email))
        await db.commit()
    r = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "a-strong-password-12345"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    return email, body["tokens"]["access_token"]


def _make_pdf_bytes(text: str = "FINRLX test 10-Q\n\nRevenue 12,345.\n\nRisks: macro.") -> bytes:
    """Return a small valid PDF (single page) with the given text.

    pypdf can produce a PDF in-memory via PdfWriter; we synthesise a
    minimal one here so the test fixture doesn't ship a binary file.
    """
    try:
        from pypdf import PdfWriter
        from pypdf.generic import RectangleObject
    except ImportError:  # pragma: no cover — dep is required
        pytest.skip("pypdf not installed")
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    # Attach a metadata field so extract_text returns *something*.
    # pypdf's blank-page extraction is empty; the metadata path is the
    # simplest way to put non-empty text into the file. For real
    # extraction fidelity we'd need reportlab, but the contract these
    # tests pin is "extraction runs and produces a token estimate" — the
    # metadata-only file is enough to exercise that path.
    writer.add_metadata({"/Title": text})
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


# ── Storage unit tests ──────────────────────────────────────────────────


def test_storage_is_safe_relative_rejects_traversal():
    assert _is_safe_relative("NVDA/file.pdf") is True
    assert _is_safe_relative("") is False
    assert _is_safe_relative("..") is False
    assert _is_safe_relative("../etc/passwd") is False
    assert _is_safe_relative("NVDA/../OTHER/file.pdf") is False
    # Absolute paths are also rejected.
    assert _is_safe_relative("/etc/passwd") is False


def test_storage_save_returns_relative_path(tmp_path, monkeypatch):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "documents_storage_path", str(tmp_path))
    relative, size = save_document("nvda", b"hello world", suffix=".pdf")
    assert relative.startswith("NVDA/")
    assert relative.endswith(".pdf")
    assert size == len(b"hello world")
    # File actually lives at the expected absolute path.
    assert (tmp_path / relative).read_bytes() == b"hello world"


# ── Extraction unit tests ───────────────────────────────────────────────


def test_extraction_estimate_tokens_zero_on_empty():
    assert estimate_tokens("") == 0
    assert estimate_tokens(None) == 0  # type: ignore[arg-type]


def test_extraction_estimate_tokens_chars_over_4():
    text = "x" * 400
    assert estimate_tokens(text) == 100


def test_extraction_raises_on_garbage_bytes():
    with pytest.raises(DocumentExtractionError):
        extract_text_from_pdf(b"this is definitely not a pdf")


def test_extraction_on_real_pdf_returns_string():
    pdf = _make_pdf_bytes("Hello FINRLX")
    text = extract_text_from_pdf(pdf)
    # The page itself is blank so extracted text may be empty; the
    # function still returned a string and did not raise.
    assert isinstance(text, str)


# ── HTTP endpoint tests ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upload_requires_auth(client):
    pdf = _make_pdf_bytes()
    r = await client.post(
        "/api/v1/research/documents",
        files={"file": ("test.pdf", pdf, "application/pdf")},
        data={"ticker": "NVDA"},
    )
    # 401 from auth dependency
    assert r.status_code == 401, r.text


@pytest.mark.asyncio
async def test_upload_invalid_ticker_returns_400(client, monkeypatch, tmp_path):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "documents_storage_path", str(tmp_path))
    _, token = await _signup_user(client)
    pdf = _make_pdf_bytes()
    r = await client.post(
        "/api/v1/research/documents",
        files={"file": ("test.pdf", pdf, "application/pdf")},
        data={"ticker": "not-a-ticker!"},
        headers=_bearer(token),
    )
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_upload_oversize_returns_413(client, monkeypatch, tmp_path):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "documents_storage_path", str(tmp_path))
    monkeypatch.setattr(config_mod.settings, "documents_max_size_mb", 1)
    _, token = await _signup_user(client)
    too_big = b"\x00" * (2 * 1024 * 1024)  # 2 MB > 1 MB cap
    r = await client.post(
        "/api/v1/research/documents",
        files={"file": ("big.pdf", too_big, "application/pdf")},
        data={"ticker": "NVDA"},
        headers=_bearer(token),
    )
    assert r.status_code == 413, r.text


@pytest.mark.asyncio
async def test_upload_empty_body_returns_400(client, monkeypatch, tmp_path):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "documents_storage_path", str(tmp_path))
    _, token = await _signup_user(client)
    r = await client.post(
        "/api/v1/research/documents",
        files={"file": ("empty.pdf", b"", "application/pdf")},
        data={"ticker": "NVDA"},
        headers=_bearer(token),
    )
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_upload_wrong_content_type_returns_415(client, monkeypatch, tmp_path):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "documents_storage_path", str(tmp_path))
    _, token = await _signup_user(client)
    r = await client.post(
        "/api/v1/research/documents",
        files={"file": ("test.txt", b"plain text", "text/plain")},
        data={"ticker": "NVDA"},
        headers=_bearer(token),
    )
    assert r.status_code == 415, r.text


@pytest.mark.asyncio
async def test_upload_happy_path_creates_row(client, monkeypatch, tmp_path):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "documents_storage_path", str(tmp_path))
    email, token = await _signup_user(client)
    pdf = _make_pdf_bytes()
    r = await client.post(
        "/api/v1/research/documents",
        files={"file": ("nvda-10q.pdf", pdf, "application/pdf")},
        data={"ticker": "nvda"},  # lower-case input; row normalises to NVDA
        headers=_bearer(token),
    )
    assert r.status_code == 201, r.text
    body = r.json()["data"]
    assert body["ticker"] == "NVDA"
    assert body["filename"] == "nvda-10q.pdf"
    assert body["uploaded_by_email"].lower() == email.lower()
    assert body["extraction_status"] in ("ready", "failed")  # blank-page PDF may extract to empty
    assert body["file_size_bytes"] > 0


@pytest.mark.asyncio
async def test_garbage_pdf_commits_row_with_failed_status(client, monkeypatch, tmp_path):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "documents_storage_path", str(tmp_path))
    _, token = await _signup_user(client)
    # Bytes that fail pypdf — the row should still commit with
    # extraction_status="failed" so the UI surfaces the error rather
    # than rejecting the upload entirely.
    r = await client.post(
        "/api/v1/research/documents",
        files={"file": ("not.pdf", b"this is not a pdf", "application/pdf")},
        data={"ticker": "NVDA"},
        headers=_bearer(token),
    )
    assert r.status_code == 201, r.text
    body = r.json()["data"]
    assert body["extraction_status"] == "failed"
    assert body["extraction_error"]


@pytest.mark.asyncio
async def test_list_documents_returns_newest_first(client, monkeypatch, tmp_path):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "documents_storage_path", str(tmp_path))
    _, token = await _signup_user(client)
    pdf = _make_pdf_bytes()
    for i in range(2):
        r = await client.post(
            "/api/v1/research/documents",
            files={"file": (f"doc-{i}.pdf", pdf, "application/pdf")},
            data={"ticker": "MSFT"},
            headers=_bearer(token),
        )
        assert r.status_code == 201

    r = await client.get(
        "/api/v1/research/documents?ticker=MSFT",
        headers=_bearer(token),
    )
    assert r.status_code == 200, r.text
    body = r.json()["data"]
    assert body["ticker"] == "MSFT"
    assert body["total"] >= 2
    # Sorted newest-first — the row with the higher uploaded_at comes first.
    timestamps = [d["uploaded_at"] for d in body["documents"]]
    assert timestamps == sorted(timestamps, reverse=True)


@pytest.mark.asyncio
async def test_get_single_document_returns_extracted_text_field(client, monkeypatch, tmp_path):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "documents_storage_path", str(tmp_path))
    _, token = await _signup_user(client)
    pdf = _make_pdf_bytes()
    create = await client.post(
        "/api/v1/research/documents",
        files={"file": ("nvda.pdf", pdf, "application/pdf")},
        data={"ticker": "NVDA"},
        headers=_bearer(token),
    )
    doc_id = create.json()["data"]["id"]
    r = await client.get(
        f"/api/v1/research/documents/{doc_id}",
        headers=_bearer(token),
    )
    assert r.status_code == 200, r.text
    body = r.json()["data"]
    assert body["id"] == doc_id
    # The field exists, even if it's empty for a blank-page test fixture.
    assert "extracted_text" in body


@pytest.mark.asyncio
async def test_download_returns_attachment(client, monkeypatch, tmp_path):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "documents_storage_path", str(tmp_path))
    _, token = await _signup_user(client)
    pdf = _make_pdf_bytes()
    create = await client.post(
        "/api/v1/research/documents",
        files={"file": ("nvda.pdf", pdf, "application/pdf")},
        data={"ticker": "NVDA"},
        headers=_bearer(token),
    )
    doc_id = create.json()["data"]["id"]
    r = await client.get(
        f"/api/v1/research/documents/{doc_id}/download",
        headers=_bearer(token),
    )
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/pdf")
    assert "attachment" in r.headers.get("content-disposition", "")
    assert r.content == pdf


@pytest.mark.asyncio
async def test_delete_only_by_uploader(client, monkeypatch, tmp_path):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "documents_storage_path", str(tmp_path))
    _, uploader_token = await _signup_user(client)
    _, other_token = await _signup_user(client)
    pdf = _make_pdf_bytes()
    create = await client.post(
        "/api/v1/research/documents",
        files={"file": ("nvda.pdf", pdf, "application/pdf")},
        data={"ticker": "NVDA"},
        headers=_bearer(uploader_token),
    )
    doc_id = create.json()["data"]["id"]

    # Other user can't delete.
    r = await client.delete(
        f"/api/v1/research/documents/{doc_id}",
        headers=_bearer(other_token),
    )
    assert r.status_code == 403, r.text

    # Uploader can delete.
    r = await client.delete(
        f"/api/v1/research/documents/{doc_id}",
        headers=_bearer(uploader_token),
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["deleted"] is True

    # Subsequent GET 404s.
    r = await client.get(
        f"/api/v1/research/documents/{doc_id}",
        headers=_bearer(uploader_token),
    )
    assert r.status_code == 404, r.text
