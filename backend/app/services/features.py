"""Feature computation service.

Phase 4B: converts ingested DB data (market_bars, news_events) into
persisted feature sets with completeness and freshness metadata.

Feature families:
  - Price momentum: return_5d, return_20d, return_60d
  - Volatility: volatility_20d
  - Drawdown: drawdown_20d
  - Volume: relative_volume_20d
  - News sentiment: news_sentiment_7d, news_count_7d
"""
import math
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import gen_uuid
from app.models.feature import FeatureDefinition, FeatureSet, FeatureValue
from app.models.ingestion import IngestionManifest, MarketBar, NewsEvent
from app.models.reference import Asset, UniverseMembership

# ── Default feature definitions ──────────────────────────────────────

DEFAULT_DEFINITIONS = [
    {"key": "return_5d",  "name": "5-Day Return", "category": "momentum",
     "description": "Percentage return over last 5 trading days",
     "lookback_days": 5, "input_kind": "bars", "output_type": "float"},
    {"key": "return_20d", "name": "20-Day Return", "category": "momentum",
     "description": "Percentage return over last 20 trading days",
     "lookback_days": 20, "input_kind": "bars", "output_type": "float"},
    {"key": "return_60d", "name": "60-Day Return", "category": "momentum",
     "description": "Percentage return over last 60 trading days",
     "lookback_days": 60, "input_kind": "bars", "output_type": "float"},
    {"key": "volatility_20d", "name": "20-Day Volatility", "category": "volatility",
     "description": "Annualised volatility from 20-day daily returns std dev",
     "lookback_days": 20, "input_kind": "bars", "output_type": "float"},
    {"key": "drawdown_20d", "name": "20-Day Max Drawdown", "category": "drawdown",
     "description": "Maximum peak-to-trough drawdown over 20 trading days",
     "lookback_days": 20, "input_kind": "bars", "output_type": "float"},
    {"key": "relative_volume_20d", "name": "Relative Volume (20d)", "category": "volume",
     "description": "Latest volume divided by 20-day average volume",
     "lookback_days": 20, "input_kind": "bars", "output_type": "float"},
    {"key": "news_sentiment_7d", "name": "7-Day News Sentiment", "category": "sentiment",
     "description": "Average sentiment score over last 7 calendar days",
     "lookback_days": 7, "input_kind": "news", "output_type": "float"},
    {"key": "news_count_7d", "name": "7-Day News Count", "category": "sentiment",
     "description": "Number of news events in last 7 calendar days",
     "lookback_days": 7, "input_kind": "news", "output_type": "int"},
]


# ── Feature computation helpers ──────────────────────────────────────

def _compute_return(closes: list[float], lookback: int) -> tuple[float | None, str]:
    """Compute percentage return over lookback period. Returns (value, quality)."""
    if len(closes) < lookback + 1:
        return None, "insufficient_data"
    old = closes[-(lookback + 1)]
    new = closes[-1]
    if old == 0:
        return None, "insufficient_data"
    return round((new - old) / old, 6), "ok"


def _compute_volatility(closes: list[float], lookback: int) -> tuple[float | None, str]:
    """Compute annualised volatility from daily returns std dev."""
    if len(closes) < lookback + 1:
        return None, "insufficient_data"
    window = closes[-(lookback + 1):]
    returns = [(window[i] - window[i - 1]) / window[i - 1]
               for i in range(1, len(window)) if window[i - 1] != 0]
    if len(returns) < 5:
        return None, "insufficient_data"
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / len(returns)
    daily_std = math.sqrt(var)
    annualised = daily_std * math.sqrt(252)
    return round(annualised, 6), "ok"


def _compute_drawdown(closes: list[float], lookback: int) -> tuple[float | None, str]:
    """Compute max drawdown over lookback period."""
    if len(closes) < lookback:
        return None, "insufficient_data"
    window = closes[-lookback:]
    peak = window[0]
    max_dd = 0.0
    for c in window:
        if c > peak:
            peak = c
        dd = (peak - c) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return round(-max_dd, 6), "ok"  # negative value convention


def _compute_relative_volume(volumes: list[int], lookback: int) -> tuple[float | None, str]:
    """Compute latest volume / average of lookback volume."""
    if len(volumes) < lookback:
        return None, "insufficient_data"
    window = volumes[-lookback:]
    avg = sum(window) / len(window)
    if avg == 0:
        return None, "insufficient_data"
    return round(volumes[-1] / avg, 4), "ok"


# ── Service class ────────────────────────────────────────────────────

class FeatureService:
    """Computes features from ingested market bars and news events."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def ensure_default_definitions(self) -> int:
        """Insert default feature definitions if they don't exist. Returns count inserted."""
        inserted = 0
        for defn in DEFAULT_DEFINITIONS:
            existing = (await self.db.execute(
                select(FeatureDefinition.id).where(FeatureDefinition.key == defn["key"])
            )).scalar()
            if not existing:
                self.db.add(FeatureDefinition(id=gen_uuid(), version="v1", **defn))
                inserted += 1
        if inserted:
            await self.db.commit()
        return inserted

    async def _get_active_definitions(self) -> list[FeatureDefinition]:
        rows = (await self.db.execute(
            select(FeatureDefinition).where(FeatureDefinition.is_active == True)  # noqa: E712
        )).scalars().all()
        return list(rows)

    async def _get_universe_assets(self, universe_id: str | None) -> list[tuple[str, str]]:
        """Return [(asset_id, ticker)] for the given universe or all assets."""
        if universe_id:
            stmt = (
                select(Asset.id, Asset.ticker)
                .join(UniverseMembership, UniverseMembership.asset_id == Asset.id)
                .where(UniverseMembership.universe_id == universe_id)
            )
        else:
            stmt = select(Asset.id, Asset.ticker)
        rows = (await self.db.execute(stmt)).all()
        return [(r.id, r.ticker) for r in rows]

    async def _get_bars(self, asset_id: str, before: date, lookback: int) -> list[dict]:
        """Get up to `lookback+1` most recent bars ending on or before `before`."""
        stmt = (
            select(MarketBar.bar_date, MarketBar.close, MarketBar.volume)
            .where(MarketBar.asset_id == asset_id)
            .where(MarketBar.bar_date <= before)
            .where(MarketBar.interval == "1d")
            .order_by(MarketBar.bar_date.desc())
            .limit(lookback + 1)
        )
        rows = (await self.db.execute(stmt)).all()
        # Return in chronological order
        return [{"date": r.bar_date, "close": r.close, "volume": r.volume} for r in reversed(rows)]

    async def _query_ticker_news(self, ticker: str, before: date, lookback_days: int) -> tuple[list[float], bool]:
        """Query news scores for a ticker in the lookback window.

        Returns (scores, source_exists) where:
        - scores: list of sentiment_score values for this ticker
        - source_exists: True if the DB has any news events at all in this window
          (regardless of ticker), meaning the news source is available
        """
        cutoff = before - timedelta(days=lookback_days)
        dt_from = datetime(cutoff.year, cutoff.month, cutoff.day, tzinfo=UTC)
        dt_to = datetime(before.year, before.month, before.day, tzinfo=UTC) + timedelta(days=1)

        # SQLite JSON contains doesn't work reliably — load all recent news, filter in Python
        stmt = (
            select(NewsEvent.sentiment_score, NewsEvent.tickers)
            .where(NewsEvent.published_at >= dt_from)
            .where(NewsEvent.published_at < dt_to)
        )
        all_rows = (await self.db.execute(stmt)).all()

        source_exists = len(all_rows) > 0
        scores = []
        for r in all_rows:
            tickers_list = r.tickers if isinstance(r.tickers, list) else []
            if ticker in tickers_list and r.sentiment_score is not None:
                scores.append(r.sentiment_score)

        return scores, source_exists

    async def _get_news_sentiment(self, ticker: str, before: date, lookback_days: int) -> tuple[float | None, str]:
        """Average sentiment for a ticker. Returns (value, quality).

        Zero ticker-specific news → insufficient_data (cannot compute a mean).
        """
        scores, _ = await self._query_ticker_news(ticker, before, lookback_days)
        if not scores:
            return None, "insufficient_data"
        avg = sum(scores) / len(scores)
        return round(avg, 4), "ok"

    async def _get_news_count(self, ticker: str, before: date, lookback_days: int) -> tuple[float, str]:
        """Count of news events for a ticker. Returns (value, quality).

        If the news source data exists (any news in the window), zero ticker-
        specific news is a truthful zero, not missing data.
        """
        scores, source_exists = await self._query_ticker_news(ticker, before, lookback_days)
        if not source_exists:
            return 0.0, "insufficient_data"
        return float(len(scores)), "ok"

    async def _get_source_manifests(self) -> list[str]:
        """Get IDs of latest completed ingestion manifests for lineage."""
        stmt = (
            select(IngestionManifest.id)
            .where(IngestionManifest.status == "completed")
            .order_by(IngestionManifest.completed_at.desc())
            .limit(10)
        )
        rows = (await self.db.execute(stmt)).all()
        return [r.id for r in rows]

    async def compute_features(
        self,
        universe_id: str | None = None,
        as_of: date | None = None,
    ) -> FeatureSet:
        """Compute all active features for all assets, reading from DB market_bars and news_events."""
        now = datetime.now(UTC)
        if as_of is None:
            as_of = date.today()

        await self.ensure_default_definitions()
        definitions = await self._get_active_definitions()
        assets = await self._get_universe_assets(universe_id)
        manifests = await self._get_source_manifests()

        fs = FeatureSet(
            id=gen_uuid(), universe_id=universe_id, as_of=as_of,
            status="computing", feature_version="v1",
            source_manifest_ids=manifests,
            started_at=now,
        )
        self.db.add(fs)

        if not assets:
            fs.status = "failed"
            fs.warnings = ["No assets found"]
            fs.completed_at = datetime.now(UTC)
            await self.db.commit()
            return fs

        warnings: list[str] = []
        total_values = 0
        ok_values = 0

        for asset_id, ticker in assets:
            # Load bars once for this asset (max lookback needed = 61 for return_60d)
            bars = await self._get_bars(asset_id, as_of, 61)
            closes = [b["close"] for b in bars]
            volumes = [b["volume"] for b in bars]

            for defn in definitions:
                value = None
                quality = "ok"
                unit = None
                window = defn.lookback_days

                if defn.key.startswith("return_"):
                    value, quality = _compute_return(closes, window)
                    unit = "pct"
                elif defn.key == "volatility_20d":
                    value, quality = _compute_volatility(closes, window)
                    unit = "ratio"
                elif defn.key == "drawdown_20d":
                    value, quality = _compute_drawdown(closes, window)
                    unit = "pct"
                elif defn.key == "relative_volume_20d":
                    value, quality = _compute_relative_volume(volumes, window)
                    unit = "ratio"
                elif defn.key == "news_sentiment_7d":
                    value, quality = await self._get_news_sentiment(ticker, as_of, window)
                    unit = "score"
                elif defn.key == "news_count_7d":
                    value, quality = await self._get_news_count(ticker, as_of, window)
                    unit = "count"

                if quality == "insufficient_data":
                    if defn.input_kind == "news":
                        warnings.append(f"{ticker}/{defn.key}: no ticker-specific news in {window}d window")
                    else:
                        warnings.append(f"{ticker}/{defn.key}: insufficient data (need {window}d, have {len(closes)-1}d bars)")

                self.db.add(FeatureValue(
                    id=gen_uuid(), feature_set_id=fs.id,
                    asset_id=asset_id, ticker=ticker,
                    feature_key=defn.key, value=value,
                    unit=unit, window_days=window, quality=quality,
                ))
                total_values += 1
                if quality == "ok":
                    ok_values += 1

        completeness = ok_values / total_values if total_values > 0 else 0.0
        fs.asset_count = len(assets)
        fs.feature_count = total_values
        fs.completeness_score = round(completeness, 4)
        fs.warnings = warnings if warnings else None
        fs.freshness_status = "healthy" if completeness > 0.8 else "degraded" if completeness > 0.5 else "stale"
        fs.status = "completed" if completeness > 0 else "failed"
        fs.completed_at = datetime.now(UTC)

        await self.db.commit()
        return fs

    async def get_feature_set(self, feature_set_id: str) -> FeatureSet | None:
        result = await self.db.execute(
            select(FeatureSet).where(FeatureSet.id == feature_set_id)
        )
        return result.scalar_one_or_none()

    async def get_feature_values(self, feature_set_id: str) -> list[FeatureValue]:
        result = await self.db.execute(
            select(FeatureValue).where(FeatureValue.feature_set_id == feature_set_id)
        )
        return list(result.scalars().all())

    async def get_latest_feature_set(self) -> FeatureSet | None:
        result = await self.db.execute(
            select(FeatureSet)
            .where(FeatureSet.status.in_(["completed", "partial"]))
            .order_by(FeatureSet.as_of.desc(), FeatureSet.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_status(self) -> dict:
        """Return feature layer status summary."""
        total_defs = (await self.db.execute(
            select(func.count()).select_from(FeatureDefinition)
        )).scalar() or 0
        active_defs = (await self.db.execute(
            select(func.count()).select_from(FeatureDefinition)
            .where(FeatureDefinition.is_active == True)  # noqa: E712
        )).scalar() or 0

        latest = await self.get_latest_feature_set()

        return {
            "latest_feature_set_id": latest.id if latest else None,
            "latest_as_of": latest.as_of if latest else None,
            "latest_status": latest.status if latest else None,
            "completeness_score": latest.completeness_score if latest else None,
            "freshness_status": latest.freshness_status if latest else None,
            "total_definitions": total_defs,
            "active_definitions": active_defs,
        }
