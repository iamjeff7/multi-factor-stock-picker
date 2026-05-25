"""Persisted experiment result schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from core.enums import ExperimentStatus, ExperimentType, PositionStatus
from core.types import (
    ConfigurationHash,
    DataVersion,
    ExperimentId,
    PositionId,
    SecurityId,
    SignalId,
    Ticker,
    TradeId,
    UniverseVersion,
)
from schemas.enums import ExitDecision, RobustnessGrade


class ExperimentMetadata(BaseModel):
    experiment_id: ExperimentId
    experiment_name: str
    experiment_type: ExperimentType
    execution_timestamp: datetime
    data_version: DataVersion
    universe_version: UniverseVersion
    configuration_hash: ConfigurationHash
    framework_version: str
    status: ExperimentStatus


class EntrySignalResultRecord(BaseModel):
    experiment_id: ExperimentId
    evaluation_date: date
    security_id: SecurityId
    ticker: Ticker
    signal_id: SignalId
    signal_version: str
    raw_signal_value: Decimal | None


class ExitSignalResultRecord(BaseModel):
    experiment_id: ExperimentId
    evaluation_date: date
    position_id: PositionId
    security_id: SecurityId
    ticker: Ticker
    signal_id: SignalId
    signal_version: str
    decision: ExitDecision
    trigger_reason: str | None = None


class FactorScoreRecord(BaseModel):
    experiment_id: ExperimentId
    evaluation_date: date
    security_id: SecurityId
    ticker: Ticker
    signal_id: SignalId
    factor_score: Decimal
    factor_rank: int | None = None


class CompositeScoreRecord(BaseModel):
    experiment_id: ExperimentId
    evaluation_date: date
    security_id: SecurityId
    ticker: Ticker
    composite_score: Decimal
    composite_rank: int | None = None


class PortfolioSelectionRecord(BaseModel):
    experiment_id: ExperimentId
    rebalance_date: date
    security_id: SecurityId
    ticker: Ticker
    portfolio_rank: int
    target_weight: Decimal
    target_shares: Decimal | None = None


class TradeRecord(BaseModel):
    experiment_id: ExperimentId
    trade_id: TradeId
    security_id: SecurityId
    ticker: Ticker
    entry_date: date
    entry_price: Decimal
    exit_date: date | None = None
    exit_price: Decimal | None = None
    shares: Decimal
    gross_pnl: Decimal | None = None
    net_pnl: Decimal | None = None
    holding_days: int | None = None
    return_pct: Decimal | None = None


class PositionRecord(BaseModel):
    experiment_id: ExperimentId
    position_id: PositionId
    security_id: SecurityId
    ticker: Ticker
    entry_date: date
    entry_price: Decimal
    shares: Decimal
    current_value: Decimal | None = None
    status: PositionStatus


class PortfolioSnapshotRecord(BaseModel):
    experiment_id: ExperimentId
    date: date
    cash: Decimal
    invested_capital: Decimal
    equity: Decimal
    portfolio_value: Decimal
    drawdown: Decimal | None = None
    number_of_positions: int


class EquityCurveRecord(BaseModel):
    experiment_id: ExperimentId
    date: date
    portfolio_value: Decimal
    daily_return: Decimal | None = None
    cumulative_return: Decimal | None = None


class BacktestSummaryRecord(BaseModel):
    experiment_id: ExperimentId
    total_return: Decimal
    annualized_return: Decimal | None = None
    cagr: Decimal | None = None
    volatility: Decimal | None = None
    sharpe_ratio: Decimal | None = None
    sortino_ratio: Decimal | None = None
    calmar_ratio: Decimal | None = None
    max_drawdown: Decimal | None = None
    win_rate: Decimal | None = None
    profit_factor: Decimal | None = None
    average_trade: Decimal | None = None
    number_of_trades: int
    turnover: Decimal | None = None


class RobustnessScoreRecord(BaseModel):
    experiment_id: ExperimentId
    robustness_score: Decimal
    stability_score: Decimal | None = None
    consistency_score: Decimal | None = None
    sample_size_score: Decimal | None = None
    overall_grade: RobustnessGrade


class ConfigurationSnapshotRecord(BaseModel):
    experiment_id: ExperimentId
    configuration_hash: ConfigurationHash
    configuration_json: dict[str, object] = Field(default_factory=dict)


class VersionMetadataRecord(BaseModel):
    experiment_id: ExperimentId
    framework_version: str
    data_version: DataVersion
    universe_version: UniverseVersion
    entry_signal_versions: dict[str, str] = Field(default_factory=dict)
    exit_signal_versions: dict[str, str] = Field(default_factory=dict)
    backtest_version: str | None = None


class StockSummaryRecord(BaseModel):
    experiment_id: ExperimentId
    security_id: SecurityId
    ticker: Ticker
    number_of_trades: int
    closed_trades: int
    open_trades: int
    total_gross_pnl: Decimal | None = None
    total_net_pnl: Decimal | None = None
    average_return_pct: Decimal | None = None
    win_rate: Decimal | None = None
    profit_factor: Decimal | None = None
    average_holding_days: Decimal | None = None
    best_trade_pnl: Decimal | None = None
    worst_trade_pnl: Decimal | None = None


class ReportArtifactRecord(BaseModel):
    experiment_id: ExperimentId
    report_id: str
    report_type: str
    generated_at: datetime
    format: str
    relative_path: str
    source_artifacts: list[str] = Field(default_factory=list)


class ExperimentReportManifest(BaseModel):
    experiment_id: ExperimentId
    artifacts: list[ReportArtifactRecord] = Field(default_factory=list)


class ExperimentSummaryRecord(BaseModel):
    experiment_id: ExperimentId
    securities_requested: int
    securities_completed: int
    securities_skipped: int
    mean_stock_return: Decimal | None = None
    median_stock_return: Decimal | None = None
    pct_stocks_positive: Decimal | None = None
    best_stock_return: Decimal | None = None
    worst_stock_return: Decimal | None = None
    number_of_trades: int
    win_rate: Decimal | None = None
    profit_factor: Decimal | None = None
    average_trade: Decimal | None = None
    total_net_pnl: Decimal | None = None
