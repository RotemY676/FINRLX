"""Ingestion domain entities.

Maps to Data Model doc 11, Domain 2: Raw and Curated Inputs.

Tables:
  market_bars   — OHLCV price bars per asset per interval
  news_events   — text/news items with source, timestamp, optional sentiment
  ingestion_manifests — tracks what was ingested, when, coverage, status
"""
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, gen_uuid


class MarketBar(Base, TimestampMixin):
    __tablename__ = "market_bars"
    __table_args__ = (
        UniqueConstraint("asset_id", "bar_date", "interval", name="uq_market_bar"),
        Index("ix_market_bar_asset_date", "asset_id", "bar_date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    asset_id: Mapped[str] = mapped_column(String(36), nullable=False)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    bar_date: Mapped[date] = mapped_column(Date, nullable=False)
    interval: Mapped[str] = mapped_column(String(10), nullable=False, default="1d")  # 1d, 1h, 5m
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="local")


class NewsEvent(Base, TimestampMixin):
    __tablename__ = "news_events"
    __table_args__ = (
        Index("ix_news_event_published", "published_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    headline: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    tickers: Mapped[list | None] = mapped_column(JSON)  # ["AAPL", "MSFT"]
    sentiment_score: Mapped[float | None] = mapped_column(Float)  # -1.0 to 1.0
    sentiment_label: Mapped[str | None] = mapped_column(String(20))  # positive, negative, neutral
    category: Mapped[str | None] = mapped_column(String(50))  # earnings, macro, sector, etc.


class IngestionManifest(Base, TimestampMixin):
    __tablename__ = "ingestion_manifests"
    __table_args__ = (
        Index("ix_manifest_source", "source"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # bars, news
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending, running, completed, partial, failed
    asset_count: Mapped[int] = mapped_column(Integer, default=0)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    date_from: Mapped[date | None] = mapped_column(Date)
    date_to: Mapped[date | None] = mapped_column(Date)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    details: Mapped[dict | None] = mapped_column(JSON)
