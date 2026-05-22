"""Phase O-0 — operator analysis archive.

Stores LLM responses the operator pastes back into FINRLX after running
context through ChatGPT or Claude in another tab. Joined to the
originating recommendation so Replay can surface them.
"""
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import gen_uuid

OPERATOR_ANALYSIS_SOURCES = ("gpt", "claude", "other")
OPERATOR_ANALYSIS_SURFACES = ("decision", "replay", "news", "manual")


class OperatorAnalysis(Base):
    __tablename__ = "operator_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_email: Mapped[str] = mapped_column(String(320), nullable=False)
    surface: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    recommendation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="other")
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
