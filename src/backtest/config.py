"""Backtest configuration models."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import model_validator

from config.models import BacktestSettings
from core.enums import PortfolioMode
from core.types import SecurityId, Ticker


class SingleStockBacktestConfig(BacktestSettings):
    """Configuration for a single-security backtest run."""

    security_id: SecurityId
    ticker: Ticker
    start_date: date
    end_date: date
    fixed_dollar_amount: Decimal | None = None
    experiment_name: str = "single_stock_backtest"

    @model_validator(mode="after")
    def validate_single_stock_settings(self) -> SingleStockBacktestConfig:
        if self.portfolio_mode is not PortfolioMode.SINGLE:
            raise ValueError("Single-stock backtests require portfolio_mode=SINGLE")
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


BacktestConfig = BacktestSettings
