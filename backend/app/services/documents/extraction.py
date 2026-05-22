"""PDF text extraction for Phase 17 research documents.

Uses `pypdf` — pure-Python, MIT-licensed, handles digital (text-based)
PDFs. Scanned 10-Q / 10-K filings would need OCR (pytesseract +
poppler); that is explicitly out of Phase 17.0 scope.

Returns a single concatenated string with form-feed (U+000C) page
boundaries so downstream consumers (Phase 17.1 LLM prompt) can do
per-page citations if needed.

The token estimate is approximate: 4 characters per token for English
text is a common rule of thumb close enough for budget tracking. The
real Anthropic API call returns exact input/output counts that the
Phase 17.1 budget tracker uses as the source of truth.
"""
from __future__ import annotations

import io


class DocumentExtractionError(RuntimeError):
    """Raised when pypdf can't parse the file (encrypted, malformed,
    truncated, etc.)."""


# Lazy import so the rest of the app doesn't pay pypdf's startup
# cost on every cold start.
def _pypdf_reader(content: bytes):
    try:
        from pypdf import PdfReader  # type: ignore[import-not-found]
    except ImportError as e:
        raise DocumentExtractionError(
            "pypdf is not installed. Add `pypdf` to backend/requirements.txt "
            "and `pip install -r requirements.txt`."
        ) from e
    try:
        return PdfReader(io.BytesIO(content))
    except Exception as e:  # pypdf raises a variety of internal types
        raise DocumentExtractionError(f"failed to open PDF: {e}") from e


def extract_text_from_pdf(content: bytes) -> str:
    """Extract concatenated text from every page.

    Pages are joined with a form-feed character (U+000C) so a future
    page-citation feature can split on it. Empty-page output is
    skipped silently (some financial filings have cover-page-only
    images that yield empty extraction without being an error).

    Raises DocumentExtractionError if the file cannot be parsed.
    """
    reader = _pypdf_reader(content)
    # Some 10-K filings ship encrypted with a blank password; pypdf can
    # handle that transparently. If decryption fails we surface the
    # error to the caller rather than returning partial text.
    if getattr(reader, "is_encrypted", False):
        try:
            reader.decrypt("")
        except Exception as e:
            raise DocumentExtractionError(
                f"PDF is encrypted and cannot be opened with a blank password: {e}"
            ) from e

    pages: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception as e:
            # Skip pages that fail to extract rather than blanking the
            # whole document. Note the error inline so the caller can
            # surface it in the analysis prompt if helpful.
            text = f"[extraction error on page: {e}]"
        text = text.strip()
        if text:
            pages.append(text)
    return "\f".join(pages)


def estimate_tokens(text: str) -> int:
    """Approximate token count for budget tracking.

    Uses the 4-chars-per-token heuristic — adequate for English
    financial text within ~10% of real tokenisation. Real Anthropic
    calls return exact counts; this estimate is only used pre-call
    for "this document would cost ~X tokens to analyse" warnings.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)
