"""Ingestion schemas for market bars, news events, and manifests.

Maps to Doc 11 Domain 2 and Doc 12 Section 7.
"""
from datetime import date, datetime
from pydantic import BaseModel, Field


# ── Market Bar ───────────────────────────────────────────────────────

class MarketBarResponse(BaseModel):
    id: str
    asset_id: str
    ticker: str
    bar_date: date
    interval: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str


class MarketBarListResponse(BaseModel):
    items: list[MarketBarResponse]
    total: int
    ticker: str | None = None
    date_from: date | None = None
    date_to: date | None = None


# ── News Event ───────────────────────────────────────────────────────

class NewsEventResponse(BaseModel):
    id: str
    headline: str
    body: str | None = None
    source: str
    url: str | None = None
    published_at: datetime
    tickers: list[str] | None = None
    sentiment_score: float | None = None
    sentiment_label: str | None = None
    category: str | None = None


class NewsEventListResponse(BaseModel):
    items: list[NewsEventResponse]
    total: int


# ── Ingestion Manifest ───────────────────────────────────────────────

class ManifestResponse(BaseModel):
    id: str
    source: str
    kind: str
    status: str
    asset_count: int
    row_count: int
    date_from: date | None = None
    date_to: date | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None


class ManifestListResponse(BaseModel):
    items: list[ManifestResponse]
    total: int


# ── Ingestion Status ─────────────────────────────────────────────────

class SourceFreshness(BaseModel):
    source: str
    kind: str
    status: str  # healthy, stale, partial, failed, missing
    last_completed: datetime | None = None
    row_count: int = 0
    date_from: date | None = None
    date_to: date | None = None


class IngestionStatusResponse(BaseModel):
    sources: list[SourceFreshness]
    total_bar_count: int = 0
    total_news_count: int = 0


# ── Ingestion Trigger ────────────────────────────────────────────────

class IngestBarsRequest(BaseModel):
    source: str = "local"
    tickers: list[str] | None = None  # None = all assets
    date_from: date | None = None
    date_to: date | None = None


class IngestNewsRequest(BaseModel):
    source: str = "local"
    date_from: date | None = None
    date_to: date | None = None


class IngestTriggerResult(BaseModel):
    manifest_id: str
    status: str
    rows_ingested: int
    message: str
