"""Multi-stock experiment configuration."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from backtest.config import SingleStockBacktestConfig
from config.models import BacktestSettings
from core.enums import PortfolioMode
from core.types import SecurityId, Ticker


class ExperimentSecurity(BaseModel):
    security_id: SecurityId
    ticker: Ticker


class SignalConfig(BaseModel):
    name: str
    params: dict[str, object] = Field(default_factory=dict)


class SingleFactorExperimentConfig(BacktestSettings):
    """Configuration for a cross-sectional single-factor experiment."""

    experiment_name: str = "single_factor_experiment"
    start_date: date
    end_date: date
    securities: list[ExperimentSecurity] = Field(default_factory=list)
    fixed_dollar_amount: Decimal | None = None
    entry_signal: SignalConfig
    exit_signal: SignalConfig

    @model_validator(mode="after")
    def validate_experiment_settings(self) -> SingleFactorExperimentConfig:
        if self.portfolio_mode is not PortfolioMode.SINGLE:
            raise ValueError("Single-factor experiments require portfolio_mode=SINGLE")
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if not self.securities:
            raise ValueError("At least one security is required")
        return self

    def to_stock_config(self, security: ExperimentSecurity) -> SingleStockBacktestConfig:
        return SingleStockBacktestConfig(
            security_id=security.security_id,
            ticker=security.ticker,
            start_date=self.start_date,
            end_date=self.end_date,
            initial_capital=self.initial_capital,
            execution_price=self.execution_price,
            commission_pct=self.commission_pct,
            commission_per_trade=self.commission_per_trade,
            slippage_pct=self.slippage_pct,
            rebalance_frequency=self.rebalance_frequency,
            portfolio_mode=self.portfolio_mode,
            position_size_method=self.position_size_method,
            fixed_dollar_amount=self.fixed_dollar_amount,
            experiment_name=self.experiment_name,
        )
