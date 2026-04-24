"""Price chart schemas for time-series + event markers + confidence band."""
from pydantic import BaseModel, Field


class PricePoint(BaseModel):
    date: str
    price: float
    benchmark: float | None = None
    band_upper: float | None = None
    band_lower: float | None = None


class ChartEvent(BaseModel):
    date: str
    label: str
    kind: str = "neutral"  # pos, neg, neutral


class PriceChartData(BaseModel):
    ticker: str
    current_price: float
    price_return_pct: float
    benchmark_return_pct: float | None = None
    benchmark_name: str = "S&P 500"
    points: list[PricePoint]
    events: list[ChartEvent] = Field(default_factory=list)
