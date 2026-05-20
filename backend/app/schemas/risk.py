"""Phase B1 — risk metrics schemas."""
from pydantic import BaseModel, Field


class SectorWeight(BaseModel):
    sector: str
    weight: float


class ConcentrationBlock(BaseModel):
    total_positions: int
    top1_weight: float
    top3_weight: float
    top5_weight: float
    sectors: list[SectorWeight] = Field(default_factory=list)


class DrawdownBlock(BaseModel):
    current_drawdown: float
    max_drawdown: float
    peak_value: float | None
    current_value: float | None


class VaRBlock(BaseModel):
    sample_size: int
    var_95: float
    var_99: float
    volatility_daily: float


class ExposureBlock(BaseModel):
    long_weight: float
    short_weight: float
    gross_exposure: float
    net_exposure: float
    cash_weight: float


class RiskBundle(BaseModel):
    portfolio_id: str
    portfolio_name: str
    concentration: ConcentrationBlock
    drawdown: DrawdownBlock
    var: VaRBlock = Field(..., alias="var")
    exposure: ExposureBlock
    snapshot_count: int

    model_config = {"populate_by_name": True}
