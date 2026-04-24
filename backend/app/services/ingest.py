"""Ingestion service with deterministic local adapter.

Phase 4A: introduces the ingestion contract and internal data flow.
Uses a local/mock adapter that generates deterministic OHLCV bars and
news events so the pipeline is testable and repeatable.

Real external adapters (e.g. Alpha Vantage, Polygon, Reuters) will be
added in a future phase without changing the service interface.
"""
import hashlib
import random
from datetime import date, datetime, timezone, timedelta

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingestion import MarketBar, NewsEvent, IngestionManifest
from app.models.reference import Asset
from app.models.base import gen_uuid


# ── Deterministic local adapter ──────────────────────────────────────


def _stable_seed(*parts: str) -> int:
    """Return a stable integer seed from arbitrary string parts.

    Uses SHA-256 so the result is identical across Python processes,
    platforms, and versions (unlike the built-in hash()).
    """
    raw = "|".join(str(p) for p in parts)
    return int(hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16], 16)


# Baseline prices for our 10 assets (used as random walk starting points)
_BASE_PRICES: dict[str, float] = {
    "AAPL": 195.0, "MSFT": 420.0, "GOOGL": 175.0, "AMZN": 185.0,
    "JPM": 198.0, "JNJ": 155.0, "XOM": 105.0, "PG": 165.0,
    "NVDA": 920.0, "V": 280.0,
}

_NEWS_TEMPLATES = [
    ("{ticker} reports quarterly earnings beat, revenue up {pct}%", "earnings", "positive"),
    ("{ticker} faces regulatory scrutiny in {region}", "regulatory", "negative"),
    ("Analysts upgrade {ticker} citing {reason}", "analyst", "positive"),
    ("{ticker} announces {amount}B share buyback program", "corporate", "positive"),
    ("Sector rotation pressures {ticker} as investors shift to {sector}", "macro", "negative"),
    ("{ticker} expands into {market}, shares rise {pct}%", "corporate", "positive"),
    ("Supply chain concerns weigh on {ticker} outlook", "supply_chain", "negative"),
    ("{ticker} dividend raised {pct}%, signals confidence", "dividend", "positive"),
]


def _generate_bars(ticker: str, asset_id: str, start: date, end: date, source: str) -> list[dict]:
    """Generate deterministic OHLCV bars for a ticker between start and end."""
    rng = random.Random(_stable_seed(ticker, str(start)))
    base = _BASE_PRICES.get(ticker, 100.0)
    price = base
    bars = []
    d = start
    while d <= end:
        # Skip weekends
        if d.weekday() >= 5:
            d += timedelta(days=1)
            continue

        daily_return = rng.gauss(0.0004, 0.018)  # slight upward drift
        price *= (1 + daily_return)
        price = max(price, 1.0)  # floor

        intraday_range = price * rng.uniform(0.008, 0.03)
        o = round(price + rng.uniform(-intraday_range / 2, intraday_range / 2), 2)
        h = round(max(o, price) + rng.uniform(0, intraday_range / 2), 2)
        l = round(min(o, price) - rng.uniform(0, intraday_range / 2), 2)
        c = round(price, 2)
        vol = int(rng.gauss(20_000_000, 5_000_000))
        vol = max(vol, 100_000)

        bars.append({
            "id": gen_uuid(),
            "asset_id": asset_id,
            "ticker": ticker,
            "bar_date": d,
            "interval": "1d",
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "volume": vol,
            "source": source,
        })
        d += timedelta(days=1)

    return bars


def _generate_news(tickers: list[str], start: date, end: date, source: str) -> list[dict]:
    """Generate deterministic news events across tickers."""
    rng = random.Random(_stable_seed("news", str(start), str(end)))
    events = []
    d = start
    while d <= end:
        if d.weekday() >= 5:
            d += timedelta(days=1)
            continue

        # 1-3 news items per day
        n_items = rng.randint(1, 3)
        for _ in range(n_items):
            ticker = rng.choice(tickers)
            tpl, category, sentiment_label = rng.choice(_NEWS_TEMPLATES)
            headline = tpl.format(
                ticker=ticker,
                pct=rng.randint(2, 15),
                region=rng.choice(["EU", "US", "Asia"]),
                reason=rng.choice(["strong fundamentals", "AI growth", "market share gains"]),
                amount=rng.choice(["5", "10", "15", "25"]),
                sector=rng.choice(["tech", "healthcare", "energy"]),
                market=rng.choice(["AI services", "cloud", "automotive"]),
            )
            sentiment_score = rng.uniform(0.3, 0.9) if sentiment_label == "positive" else rng.uniform(-0.9, -0.3)

            hour = rng.randint(6, 20)
            minute = rng.randint(0, 59)
            pub_dt = datetime(d.year, d.month, d.day, hour, minute, tzinfo=timezone.utc)

            events.append({
                "id": gen_uuid(),
                "headline": headline,
                "body": None,
                "source": source,
                "url": None,
                "published_at": pub_dt,
                "tickers": [ticker],
                "sentiment_score": round(sentiment_score, 3),
                "sentiment_label": sentiment_label,
                "category": category,
            })

        d += timedelta(days=1)

    return events


# ── Service class ────────────────────────────────────────────────────

class IngestService:
    """Coordinates ingestion runs and writes manifests."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_asset_map(self, tickers: list[str] | None = None) -> dict[str, str]:
        """Return {ticker: asset_id} for requested or all assets."""
        stmt = select(Asset.id, Asset.ticker)
        if tickers:
            stmt = stmt.where(Asset.ticker.in_(tickers))
        rows = (await self.db.execute(stmt)).all()
        return {r.ticker: r.id for r in rows}

    async def ingest_bars(
        self,
        source: str = "local",
        tickers: list[str] | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> IngestionManifest:
        """Ingest OHLCV bars for the given assets and date range."""
        now = datetime.now(timezone.utc)
        if date_to is None:
            date_to = date.today()
        if date_from is None:
            date_from = date_to - timedelta(days=90)

        # Create manifest
        manifest = IngestionManifest(
            id=gen_uuid(), source=source, kind="bars",
            status="running", started_at=now,
            date_from=date_from, date_to=date_to,
        )
        self.db.add(manifest)

        asset_map = await self._get_asset_map(tickers)
        if not asset_map:
            manifest.status = "failed"
            manifest.error_message = "No matching assets found"
            manifest.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            return manifest

        total_rows = 0
        for ticker, asset_id in asset_map.items():
            bars = _generate_bars(ticker, asset_id, date_from, date_to, source)
            for bar_data in bars:
                # Check for existing bar (idempotent upsert)
                existing = (await self.db.execute(
                    select(MarketBar.id)
                    .where(MarketBar.asset_id == asset_id)
                    .where(MarketBar.bar_date == bar_data["bar_date"])
                    .where(MarketBar.interval == bar_data["interval"])
                )).scalar()
                if not existing:
                    self.db.add(MarketBar(**bar_data))
                    total_rows += 1

        manifest.status = "completed"
        manifest.asset_count = len(asset_map)
        manifest.row_count = total_rows
        manifest.completed_at = datetime.now(timezone.utc)

        await self.db.commit()
        return manifest

    async def ingest_news(
        self,
        source: str = "local",
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> IngestionManifest:
        """Ingest news events for the given date range."""
        now = datetime.now(timezone.utc)
        if date_to is None:
            date_to = date.today()
        if date_from is None:
            date_from = date_to - timedelta(days=30)

        manifest = IngestionManifest(
            id=gen_uuid(), source=source, kind="news",
            status="running", started_at=now,
            date_from=date_from, date_to=date_to,
        )
        self.db.add(manifest)

        asset_map = await self._get_asset_map()
        tickers = list(asset_map.keys())
        if not tickers:
            manifest.status = "failed"
            manifest.error_message = "No assets in database"
            manifest.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            return manifest

        events = _generate_news(tickers, date_from, date_to, source)
        inserted = 0
        for ev_data in events:
            # Idempotent: skip if same source + published_at + headline exists
            existing = (await self.db.execute(
                select(NewsEvent.id)
                .where(NewsEvent.source == ev_data["source"])
                .where(NewsEvent.published_at == ev_data["published_at"])
                .where(NewsEvent.headline == ev_data["headline"])
            )).scalar()
            if not existing:
                self.db.add(NewsEvent(**ev_data))
                inserted += 1

        manifest.status = "completed"
        manifest.asset_count = len(tickers)
        manifest.row_count = inserted
        manifest.completed_at = datetime.now(timezone.utc)

        await self.db.commit()
        return manifest

    async def get_status(self) -> dict:
        """Return ingestion freshness status per source/kind.

        Reports the latest manifest for each source+kind truthfully:
        completed + fresh => healthy, completed + old => stale,
        partial => partial, failed => failed, otherwise => missing.
        """
        # Get all manifests ordered by recency (not filtered by status)
        stmt = (
            select(
                IngestionManifest.source,
                IngestionManifest.kind,
                IngestionManifest.status,
                IngestionManifest.completed_at,
                IngestionManifest.started_at,
                IngestionManifest.row_count,
                IngestionManifest.date_from,
                IngestionManifest.date_to,
            )
            .order_by(IngestionManifest.created_at.desc())
        )
        rows = (await self.db.execute(stmt)).all()

        # Deduplicate to latest per source+kind
        seen = set()
        sources = []
        for r in rows:
            key = (r.source, r.kind)
            if key in seen:
                continue
            seen.add(key)

            # Determine freshness from raw manifest status
            manifest_status = r.status
            if manifest_status == "failed":
                health = "failed"
            elif manifest_status == "partial":
                health = "partial"
            elif manifest_status == "running":
                health = "partial"
            elif manifest_status == "completed":
                ref_time = r.completed_at or r.started_at
                if ref_time:
                    age = datetime.now(timezone.utc) - ref_time.replace(tzinfo=timezone.utc)
                    health = "stale" if age > timedelta(hours=24) else "healthy"
                else:
                    health = "healthy"
            else:
                health = "missing"

            sources.append({
                "source": r.source,
                "kind": r.kind,
                "status": health,
                "last_completed": r.completed_at,
                "row_count": r.row_count or 0,
                "date_from": r.date_from,
                "date_to": r.date_to,
            })

        # Totals
        bar_count = (await self.db.execute(
            select(func.count()).select_from(MarketBar)
        )).scalar() or 0
        news_count = (await self.db.execute(
            select(func.count()).select_from(NewsEvent)
        )).scalar() or 0

        return {
            "sources": sources,
            "total_bar_count": bar_count,
            "total_news_count": news_count,
        }

    async def get_manifests(self, source: str | None = None) -> list[IngestionManifest]:
        """Return ingestion manifests, optionally filtered by source."""
        stmt = select(IngestionManifest).order_by(IngestionManifest.created_at.desc()).limit(50)
        if source:
            stmt = stmt.where(IngestionManifest.source == source)
        return list((await self.db.execute(stmt)).scalars().all())
