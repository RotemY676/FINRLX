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
    calmar_ratio: float | None = None
    volatility: float | None = None
    total_trades: int | None = None
    avg_turnover: float | None = None


class EquityCurvePoint(BaseModel):
    date: str
    value: float


class BacktestDecisionPoint(BaseModel):
    date: str
    recommendation_id: str | None = None
    positions: int = 0
    turnover: float = 0.0


class BacktestProvenance(BaseModel):
    recommendation_ids: list[str] = Field(default_factory=list)
    source_feature_set_ids: list[str] = Field(default_factory=list)
    source_signal_run_ids: list[str] = Field(default_factory=list)
    market_bar_window: dict | None = None
    rebalance_dates: list[str] = Field(default_factory=list)
    created_by_service: str | None = None


class BacktestDetail(BaseModel):
    id: str
    name: str
    status: str
    source_type: str = "unknown"  # pipeline_backtest, seed_demo, unknown
    is_demo: bool = True
    lineage_available: bool = False
    universe_name: str | None = None
    policy_version_id: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_promoted: bool
    config: dict = Field(default_factory=dict)
    results: BacktestResultSummary
    equity_curve: list[EquityCurvePoint] = Field(default_factory=list)
    decision_points: list[BacktestDecisionPoint] = Field(default_factory=list)
    provenance: BacktestProvenance | None = None
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime


class BacktestListItem(BaseModel):
    id: str
    name: str
    status: str
    source_type: str = "unknown"
    is_demo: bool = True
    lineage_available: bool = False
    decision_count: int = 0
    warning_count: int = 0
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
    start_date: str | None = None
    end_date: str | None = None
    universe_id: str | None = None
    rebalance_frequency: str = "monthly"
    cost_bps: int = 10


class BacktestStatusResponse(BaseModel):
    total: int = 0
    completed: int = 0
