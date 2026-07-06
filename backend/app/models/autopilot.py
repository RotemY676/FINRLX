"""LEAP S2 — persisted autopilot dossiers (D34: cache + persistence).

One row per (ticker); the latest dossier payload is upserted whenever the
pipeline produces a fresh build. Historical dossier retention is a debt row
(see STATE_OF_THE_PRODUCT), latest-per-ticker is what Simple Mode and the
comparison endpoint need.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, gen_uuid


class AutopilotDossier(Base, TimestampMixin):
    __tablename__ = "autopilot_dossiers"
    __table_args__ = (Index("ix_autopilot_dossier_ticker", "ticker", unique=True),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    latest_bar_date: Mapped[str] = mapped_column(String(10), nullable=False)
    config_version: Mapped[str] = mapped_column(String(40), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
