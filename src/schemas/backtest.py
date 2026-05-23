"""Backtest domain schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from core.types import SecurityId, Ticker, TradeId


class Trade(BaseModel):
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


class PortfolioSnapshot(BaseModel):
    date: date
    cash: Decimal
    equity: Decimal
    portfolio_value: Decimal
    drawdown: Decimal | None = None
    number_of_positions: int


class EquityCurvePoint(BaseModel):
    date: date
    portfolio_value: Decimal
    daily_return: Decimal | None = None
    cumulative_return: Decimal | None = None


class BacktestSummary(BaseModel):
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
