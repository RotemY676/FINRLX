"""Phase B1 — risk metrics for paper portfolios.

Computes VaR / concentration / drawdown / exposure from existing paper
portfolio data. No new tables, no new ingest — every metric reads from
PaperPortfolio + PaperValuationSnapshot + the holdings dict.

The metrics are intentionally simple and stand on their own without
external benchmarks (so e.g. portfolio beta is *not* computed here —
that requires a market series and belongs to a later phase).
"""
from __future__ import annotations

import math
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reference import Asset
from app.models.validation import PaperPortfolio, PaperValuationSnapshot

# z-scores for one-tailed parametric VaR
_Z = {0.95: 1.6449, 0.99: 2.3263}


def _stddev(xs: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / (n - 1)
    return math.sqrt(var)


class RiskMetricsService:
    """Compute risk metrics for paper portfolios.

    Inputs already in the DB:
      - PaperPortfolio.current_holdings (dict of asset_id → {ticker, target_weight, current_weight, ...})
      - PaperValuationSnapshot rows with daily_return, max_drawdown_to_date
      - Asset.sector for sector concentration

    Each method returns a Python dict that the API layer wraps in a
    Pydantic schema. No I/O outside the AsyncSession.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_risk_bundle(self, portfolio_id: str) -> dict | None:
        pp = (await self.db.execute(
            select(PaperPortfolio).where(PaperPortfolio.id == portfolio_id)
        )).scalar_one_or_none()
        if pp is None:
            return None

        holdings = pp.current_holdings or {}

        snapshots = (await self.db.execute(
            select(PaperValuationSnapshot)
            .where(PaperValuationSnapshot.portfolio_id == portfolio_id)
            .order_by(PaperValuationSnapshot.valuation_date.asc())
        )).scalars().all()

        # Asset metadata for sector lookup
        asset_ids = list(holdings.keys())
        asset_rows = []
        if asset_ids:
            asset_rows = (await self.db.execute(
                select(Asset).where(Asset.id.in_(asset_ids))
            )).scalars().all()
        sector_by_asset = {a.id: (a.sector or "Unclassified") for a in asset_rows}

        return {
            "portfolio_id": portfolio_id,
            "portfolio_name": pp.name,
            "concentration": self._concentration(holdings, sector_by_asset),
            "drawdown": self._drawdown(snapshots),
            "var": self._var(snapshots),
            "exposure": self._exposure(holdings, pp.cash_weight),
            "snapshot_count": len(snapshots),
        }

    # ── Internals ──────────────────────────────────────────────────────

    def _concentration(
        self, holdings: dict, sector_by_asset: dict[str, str]
    ) -> dict:
        rows = []
        for aid, info in holdings.items():
            w = float(info.get("current_weight", info.get("target_weight", 0.0)))
            rows.append({"asset_id": aid, "ticker": info.get("ticker", aid[:8]), "weight": w})
        rows.sort(key=lambda r: r["weight"], reverse=True)

        top1 = rows[0]["weight"] if rows else 0.0
        top3 = sum(r["weight"] for r in rows[:3])
        top5 = sum(r["weight"] for r in rows[:5])

        sector_totals: dict[str, float] = defaultdict(float)
        for r in rows:
            sec = sector_by_asset.get(r["asset_id"], "Unclassified")
            sector_totals[sec] += r["weight"]
        sectors = sorted(
            [{"sector": k, "weight": v} for k, v in sector_totals.items()],
            key=lambda s: s["weight"],
            reverse=True,
        )

        return {
            "total_positions": len(rows),
            "top1_weight": round(top1, 4),
            "top3_weight": round(top3, 4),
            "top5_weight": round(top5, 4),
            "sectors": [{"sector": s["sector"], "weight": round(s["weight"], 4)} for s in sectors],
        }

    def _drawdown(self, snapshots: list[PaperValuationSnapshot]) -> dict:
        if not snapshots:
            return {"current_drawdown": 0.0, "max_drawdown": 0.0, "peak_value": None, "current_value": None}
        values = [s.portfolio_value for s in snapshots]
        peak = max(values)
        current = values[-1]
        current_dd = (current - peak) / peak if peak > 0 else 0.0
        # max_drawdown_to_date on the last snapshot is the running max; fall back to computing.
        max_dd_field = snapshots[-1].max_drawdown_to_date
        if max_dd_field is None:
            running_peak = values[0]
            worst = 0.0
            for v in values:
                if v > running_peak:
                    running_peak = v
                dd = (v - running_peak) / running_peak if running_peak > 0 else 0.0
                if dd < worst:
                    worst = dd
            max_dd_field = worst
        return {
            "current_drawdown": round(current_dd, 4),
            "max_drawdown": round(float(max_dd_field), 4),
            "peak_value": round(peak, 2),
            "current_value": round(current, 2),
        }

    def _var(self, snapshots: list[PaperValuationSnapshot]) -> dict:
        returns = [s.daily_return for s in snapshots if s.daily_return is not None]
        n = len(returns)
        if n < 2:
            return {"sample_size": n, "var_95": 0.0, "var_99": 0.0, "volatility_daily": 0.0}
        sigma = _stddev(returns)
        return {
            "sample_size": n,
            "var_95": round(_Z[0.95] * sigma, 6),
            "var_99": round(_Z[0.99] * sigma, 6),
            "volatility_daily": round(sigma, 6),
        }

    def _exposure(self, holdings: dict, cash_weight: float) -> dict:
        long_weight = 0.0
        short_weight = 0.0
        for info in holdings.values():
            w = float(info.get("current_weight", info.get("target_weight", 0.0)))
            if w >= 0:
                long_weight += w
            else:
                short_weight += abs(w)
        invested = long_weight + short_weight
        return {
            "long_weight": round(long_weight, 4),
            "short_weight": round(short_weight, 4),
            "gross_exposure": round(invested, 4),
            "net_exposure": round(long_weight - short_weight, 4),
            "cash_weight": round(float(cash_weight or 0.0), 4),
        }
