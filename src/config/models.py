"""Pydantic models for YAML configuration files."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from core.enums import (
    Exchange,
    ExecutionPrice,
    PortfolioMode,
    PositionSizeMethod,
    RebalanceFrequency,
    SecurityType,
)


class DataSettings(BaseModel):
    raw_dir: Path = Path("data/raw")
    processed_dir: Path = Path("data/processed")
    cache_dir: Path = Path("data/cache")
    data_version: str = "data_001"


class UniverseSettings(BaseModel):
    allowed_exchanges: list[Exchange] = Field(
        default_factory=lambda: [Exchange.NYSE, Exchange.NASDAQ, Exchange.NYSE_AMERICAN]
    )
    allowed_security_types: list[SecurityType] = Field(
        default_factory=lambda: [SecurityType.COMMON_STOCK]
    )
    min_price: float = 5.00
    min_average_daily_dollar_volume: float = 1_000_000
    min_market_cap: float | None = None
    minimum_trading_history_days: int = 252


class BacktestSettings(BaseModel):
    initial_capital: float = 100_000
    execution_price: ExecutionPrice = ExecutionPrice.NEXT_OPEN
    commission_pct: float = 0.0
    commission_per_trade: float | None = None
    slippage_pct: float = 0.001
    rebalance_frequency: RebalanceFrequency = RebalanceFrequency.MONTHLY
    portfolio_mode: PortfolioMode = PortfolioMode.TOP_N
    position_size_method: PositionSizeMethod = PositionSizeMethod.EQUAL_WEIGHT


class AppConfig(BaseModel):
    framework_version: str = "2.0.0"
    data_dir: Path = Path("data")
    results_dir: Path = Path("results")
    data: DataSettings = Field(default_factory=DataSettings)
    universe: UniverseSettings = Field(default_factory=UniverseSettings)
    backtest: BacktestSettings = Field(default_factory=BacktestSettings)
    config_format: Literal["yaml"] = "yaml"
