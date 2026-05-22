"""Phase 17.1 — DocumentAnalysis + LLMTokenUsage models.

DocumentAnalysis: every operator question against a research document
(stored as `prompt` + `response`) plus the LLM provenance — provider,
model, exact token counts the provider returned, and a "good enough"
estimate of cost in USD. We DO NOT compute cost server-side at write
time (provider pricing changes); the estimate is recorded for the
budget tracker's monthly accounting and a UI hint.

LLMTokenUsage: month-bucketed totals. The budget tracker writes to
this table on every successful LLM call and reads it before the call
to enforce `MAX_MONTHLY_LLM_TOKENS`. Bucketing by (year, month,
provider) keeps the table tiny — at most one row per provider per
month per environment.

Both tables are read-only from the operator's perspective; the
analyze endpoint is the only writer.
"""
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import gen_uuid


class DocumentAnalysis(Base):
    __tablename__ = "document_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)

    # Provenance — the operator who triggered the analysis. Analyses
    # are SHARED BY TICKER along with their parent documents (anyone
    # can read), so `created_by_email` is for audit / "asked by" UI
    # labels, not for access control. Only the author can delete.
    created_by_email: Mapped[str] = mapped_column(String(320), nullable=False)

    # LLM call provenance — both stored verbatim from the provider's
    # response object. `provider` matches `app.services.llm.router`
    # names: "anthropic" | "openai" | "local" | "stub" (for failure
    # paths) so the FE can show which model produced this answer.
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Cost estimate is best-effort — the budget tracker uses a static
    # per-provider rate table. NULL means "we didn't price this call".
    cost_estimate_usd: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class LLMTokenUsage(Base):
    """Month-bucketed LLM token totals. One row per (year, month,
    provider). The budget cap reads SUM(input + output) for the current
    (year, month) and 503s when it would exceed `MAX_MONTHLY_LLM_TOKENS`.

    Indexed unique on (year, month, provider) so the budget tracker
    can upsert atomically without a transaction-level lock dance.
    """

    __tablename__ = "llm_token_usage"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    # Bucket key. We store these as ints (not a date column) because
    # the budget check is always "current month" — no range queries.
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..12
    provider: Mapped[str] = mapped_column(String(40), nullable=False)

    input_tokens_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_estimate_usd_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Updated on every accumulator write so we can show "last call was
    # X ago" in the budget endpoint's FE-facing payload.
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("year", "month", "provider", name="uq_llm_token_usage_bucket"),
    )
