"""Backtest runtime portfolio state."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from core.enums import OrderSide, PositionStatus
from core.types import ExperimentId, PositionId, SecurityId, Ticker, TradeId
from schemas.backtest import EquityCurvePoint, PortfolioSnapshot, Trade


class PendingOrder(BaseModel):
    side: OrderSide
    signal_date: date
    execution_date: date
    trigger_reason: str | None = None


class OpenPosition(BaseModel):
    position_id: PositionId
    security_id: SecurityId
    ticker: Ticker
    entry_date: date
    entry_price: Decimal
    entry_commission: Decimal
    shares: Decimal
    highest_price_since_entry: Decimal
    lowest_price_since_entry: Decimal


class PortfolioState(BaseModel):
    experiment_id: ExperimentId
    initial_capital: Decimal
    cash: Decimal
    position: OpenPosition | None = None
    pending_order: PendingOrder | None = None
    peak_portfolio_value: Decimal
    trades: list[Trade] = Field(default_factory=list)
    snapshots: list[PortfolioSnapshot] = Field(default_factory=list)
    equity_curve: list[EquityCurvePoint] = Field(default_factory=list)
    open_trade_id: TradeId | None = None


class BacktestRunResult(BaseModel):
    experiment_id: ExperimentId
    trades: list[Trade]
    snapshots: list[PortfolioSnapshot]
    equity_curve: list[EquityCurvePoint]
    positions_closed: int
    final_cash: Decimal
    final_portfolio_value: Decimal


def position_status(position: OpenPosition | None) -> PositionStatus:
    if position is None:
        return PositionStatus.CLOSED
    return PositionStatus.OPEN
