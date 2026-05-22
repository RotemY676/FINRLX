"""Research orchestration services (Phase 18.4+).

This package holds the cross-module orchestrators that compose the
single-purpose services (EDGAR, documents, LLM, budget) into the
flows the user-facing endpoints invoke.
"""
from app.services.research.auto_ingest import (
    AutoIngestResult,
    AutoIngestFailure,
    auto_ingest_filings,
)

__all__ = [
    "AutoIngestResult",
    "AutoIngestFailure",
    "auto_ingest_filings",
]
