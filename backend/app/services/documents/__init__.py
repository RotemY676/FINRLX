"""Phase 17 — Research documents service.

Two responsibilities split across submodules:
  - `storage.py` — host-filesystem layout (read/write/delete on the
    Railway volume).
  - `extraction.py` — PDF -> plain text via pypdf, with a token
    estimate suitable for the Phase 17.1 budget tracker.

The DB model lives in `app.models.document`. The API surface lives in
`app.api.v1.research_documents`.
"""
from app.services.documents.extraction import (
    extract_text_from_pdf,
    estimate_tokens,
    DocumentExtractionError,
)
from app.services.documents.storage import (
    save_document,
    open_document,
    delete_document,
    DocumentStorageError,
)

__all__ = [
    "extract_text_from_pdf",
    "estimate_tokens",
    "DocumentExtractionError",
    "save_document",
    "open_document",
    "delete_document",
    "DocumentStorageError",
]
