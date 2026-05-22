"""Filesystem storage for Phase 17 research documents.

Layout under `settings.documents_storage_path`:

    <storage_root>/
        NVDA/
            <uuid-1>.pdf
            <uuid-2>.pdf
        AAPL/
            <uuid-3>.pdf

Why filesystem and not blob storage:
  - Per the Phase 17 storage decision, we use a Railway volume mount.
    A single backend instance owns the directory.
  - Swappable later: every caller goes through this module's three
    helpers, so moving to S3 / R2 / Spaces means rewriting this file
    only.

Returns RELATIVE paths (e.g. "NVDA/<uuid>.pdf") so DB rows are
storage-location-agnostic — moving the volume mount in Railway does
not require a backfill.
"""
from __future__ import annotations

from pathlib import Path

from app.core.config import settings
from app.models.base import gen_uuid


class DocumentStorageError(RuntimeError):
    """Raised on filesystem read/write/delete failures."""


def _root() -> Path:
    """Resolve the storage root, creating it if missing."""
    root = Path(settings.documents_storage_path).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_document(ticker: str, content: bytes, suffix: str = ".pdf") -> tuple[str, int]:
    """Write `content` to `<root>/<TICKER>/<uuid><suffix>` and return
    (`relative_path`, `size_bytes`). The relative path is stored on the
    DB row; the absolute path is resolved via `open_document` on read.
    """
    upper = ticker.upper()
    try:
        ticker_dir = _root() / upper
        ticker_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{gen_uuid()}{suffix}"
        absolute = ticker_dir / filename
        absolute.write_bytes(content)
    except OSError as e:
        raise DocumentStorageError(f"failed to write document: {e}") from e
    relative = f"{upper}/{filename}"
    return relative, len(content)


def open_document(relative_path: str) -> bytes:
    """Read a previously-saved document by its relative path.

    Raises DocumentStorageError on missing file or read failure.
    """
    try:
        absolute = _root() / relative_path
        if not _is_safe_relative(relative_path):
            # Defense-in-depth — never let a relative path escape the
            # storage root via '..' or absolute resolution.
            raise DocumentStorageError("unsafe relative path rejected")
        return absolute.read_bytes()
    except FileNotFoundError as e:
        raise DocumentStorageError(f"document not found: {relative_path}") from e
    except OSError as e:
        raise DocumentStorageError(f"failed to read document: {e}") from e


def delete_document(relative_path: str) -> None:
    """Remove a document. No-op if already absent (idempotent — the DB
    row is the source of truth for "does this document exist")."""
    try:
        if not _is_safe_relative(relative_path):
            raise DocumentStorageError("unsafe relative path rejected")
        absolute = _root() / relative_path
        if absolute.exists():
            absolute.unlink()
    except OSError as e:
        raise DocumentStorageError(f"failed to delete document: {e}") from e


def _is_safe_relative(relative_path: str) -> bool:
    """Reject absolute paths and any path containing '..' segments.

    The intent is that callers always pass paths produced by
    `save_document`, which are always of the form `TICKER/<uuid>.pdf`.
    A user-supplied path that tries to escape the storage root gets
    rejected here.

    We evaluate POSIX semantics regardless of host OS so a UNIX-style
    absolute path "/etc/passwd" is rejected even when the runtime
    happens to be Windows (where `pathlib.Path("/etc/passwd").is_absolute()`
    returns False because there is no drive letter). Same for Windows
    drive prefixes when the runtime is Linux.
    """
    if not relative_path:
        return False
    # UNIX-absolute (starts with "/" or "\") — reject everywhere.
    if relative_path.startswith("/") or relative_path.startswith("\\"):
        return False
    # Windows-drive prefix (e.g. C:, D:) — reject everywhere.
    if len(relative_path) >= 2 and relative_path[1] == ":":
        return False
    # Reject any traversal segments. Use PurePosixPath so part-splitting
    # is consistent across OSes; we normalise both "/" and "\" first.
    from pathlib import PurePosixPath
    parts = PurePosixPath(relative_path.replace("\\", "/")).parts
    if any(part == ".." for part in parts):
        return False
    return True
