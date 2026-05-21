"""Phase FX-2 — translate a PaperPortfolio's holdings into a target currency.

Lives in its own module so the existing `paper.py` (large, well-tested)
stays untouched.

The flow:
  1. Load the active portfolio.
  2. For each holding, look up the underlying Asset's `currency`
     (defaults to USD if missing — same as Asset model default).
  3. Convert the holding's value through `FxService.convert(asset_ccy → target_ccy)`.
  4. Aggregate totals + carry the per-holding fx_meta for transparency.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from datetime import date as DateType

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingestion import MarketBar
from app.models.reference import Asset
from app.models.validation import PaperPortfolio
from app.services.fx_service import FxConversionError, FxService


@dataclass(frozen=True)
class HoldingValueLine:
    asset_id: str
    ticker: str
    asset_currency: str
    quantity: float
    last_price: float
    value_native: float
    value_in_base: float
    fx_rate: float
    fx_rate_date: DateType
    fx_is_fallback: bool


@dataclass
class PortfolioValuationInCurrency:
    portfolio_id: str
    base_currency: str
    target_currency: str
    as_of_date: DateType
    total_value_native_sum: float  # sum of native-currency values (NOT meaningful mixed)
    total_value_in_target: float
    holdings: list[HoldingValueLine] = field(default_factory=list)
    fx_warnings: list[str] = field(default_factory=list)


async def value_portfolio_in_currency(
    db: AsyncSession,
    portfolio: PaperPortfolio,
    target_currency: str,
    on_date: DateType | None = None,
) -> PortfolioValuationInCurrency:
    """Translate every holding into ``target_currency`` and aggregate."""
    on_date = on_date or datetime.now(UTC).date()
    holdings_dict = portfolio.current_holdings or {}
    base_currency = portfolio.base_currency or "USD"

    fx_svc = FxService(db)

    # Fetch every asset row in one go for the holdings we have
    asset_ids = list(holdings_dict.keys())
    asset_rows: dict[str, Asset] = {}
    if asset_ids:
        rows = (
            await db.execute(select(Asset).where(Asset.id.in_(asset_ids)))
        ).scalars().all()
        asset_rows = {a.id: a for a in rows}

    lines: list[HoldingValueLine] = []
    warnings: list[str] = []
    total_in_target = 0.0
    total_native_sum = 0.0

    for asset_id, payload in holdings_dict.items():
        asset = asset_rows.get(asset_id)
        ticker = (payload.get("ticker") if isinstance(payload, dict) else None) or (
            asset.ticker if asset else "?"
        )
        quantity = float((payload or {}).get("quantity", 0))
        asset_ccy = (asset.currency if asset else None) or "USD"

        # Latest known price for this asset (in its native currency)
        price_row = (
            await db.execute(
                select(MarketBar.close)
                .where(MarketBar.asset_id == asset_id)
                .order_by(MarketBar.bar_date.desc())
                .limit(1)
            )
        ).scalar()
        last_price = float(price_row) if price_row is not None else 0.0
        value_native = quantity * last_price
        total_native_sum += value_native

        # Convert native → target
        try:
            conv = await fx_svc.convert(value_native, asset_ccy, target_currency, on_date)
            value_in_target = conv.amount_out
            if conv.is_fallback and conv.fallback_reason:
                warnings.append(f"{ticker}: FX {asset_ccy}->{target_currency} {conv.fallback_reason}")
            lines.append(
                HoldingValueLine(
                    asset_id=asset_id,
                    ticker=ticker,
                    asset_currency=asset_ccy,
                    quantity=quantity,
                    last_price=last_price,
                    value_native=round(value_native, 4),
                    value_in_base=round(value_in_target, 4),
                    fx_rate=conv.rate,
                    fx_rate_date=conv.rate_date,
                    fx_is_fallback=conv.is_fallback,
                )
            )
            total_in_target += value_in_target
        except FxConversionError as exc:
            warnings.append(f"{ticker}: FX {asset_ccy}->{target_currency} unavailable ({exc})")
            lines.append(
                HoldingValueLine(
                    asset_id=asset_id,
                    ticker=ticker,
                    asset_currency=asset_ccy,
                    quantity=quantity,
                    last_price=last_price,
                    value_native=round(value_native, 4),
                    value_in_base=0.0,
                    fx_rate=0.0,
                    fx_rate_date=on_date,
                    fx_is_fallback=True,
                )
            )

    return PortfolioValuationInCurrency(
        portfolio_id=portfolio.id,
        base_currency=base_currency,
        target_currency=target_currency,
        as_of_date=on_date,
        total_value_native_sum=round(total_native_sum, 4),
        total_value_in_target=round(total_in_target, 4),
        holdings=lines,
        fx_warnings=warnings,
    )
