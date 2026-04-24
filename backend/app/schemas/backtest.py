"""Backtest schemas.

Maps to Data Model doc 11, Domain 7 and API Contract doc 12.
"""
from datetime import datetime

from pydantic import BaseModel, Field


class BacktestResultSummary(BaseModel):
    total_return: float | None = None
    annualized_return: float | None = None
    max_drawdown: float | None = None
    sharpe_ratio: float | None = None
    volatility: float | None = None
    total_trades: int | None = None
    avg_turnover: float | None = None


class EquityCurvePoint(BaseModel):
    date: str  # ISO date
    value: float  # portfolio value, base=100


class BacktestDetail(BaseModel):
    id: str
    name: str
    status: str
    universe_name: str | None = None
    policy_version_id: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_promoted: bool
    config: dict = Field(default_factory=dict)
    results: BacktestResultSummary
    equity_curve: list[EquityCurvePoint] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime


class BacktestListItem(BaseModel):
    id: str
    name: str
    status: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_promoted: bool
    total_return: float | None = None
    sharpe_ratio: float | None = None


class BacktestListResponse(BaseModel):
    items: list[BacktestListItem]
    total: int


class BacktestRunRequest(BaseModel):
    name: str = "Walk-Forward Backtest"
    start_date: str | None = None  # ISO date
    end_date: str | None = None
    universe_id: str | None = None
    rebalance_frequency: str = "monthly"  # weekly or monthly
    cost_bps: int = 10


class BacktestStatusResponse(BaseModel):
    total: int = 0
    completed: int = 0
