"""Trade lifecycle helpers."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from backtest.state import OpenPosition, PendingOrder, PortfolioState
from core.enums import OrderSide
from core.types import PositionId, SecurityId, Ticker, TradeId
from schemas.backtest import Trade
from schemas.exit import PositionContext


def build_position_context(
    position: OpenPosition,
    evaluation_date: date,
    mark_price: Decimal,
) -> PositionContext:
    unrealized = (mark_price - position.entry_price) * position.shares
    return PositionContext(
        position_id=position.position_id,
        security_id=position.security_id,
        ticker=position.ticker,
        entry_date=position.entry_date,
        entry_price=position.entry_price,
        position_size=position.shares,
        holding_period=(evaluation_date - position.entry_date).days,
        highest_price_since_entry=position.highest_price_since_entry,
        lowest_price_since_entry=position.lowest_price_since_entry,
        unrealized_pnl=unrealized,
    )


def queue_order(
    state: PortfolioState,
    side: OrderSide,
    signal_date: date,
    execution_date: date,
    trigger_reason: str | None = None,
) -> None:
    if state.pending_order is not None:
        raise ValueError("Only one pending order is supported in single-stock mode")
    state.pending_order = PendingOrder(
        side=side,
        signal_date=signal_date,
        execution_date=execution_date,
        trigger_reason=trigger_reason,
    )


def open_trade(
    state: PortfolioState,
    trade_id: TradeId,
    position_id: PositionId,
    security_id: SecurityId,
    ticker: Ticker,
    entry_date: date,
    entry_price: Decimal,
    entry_commission: Decimal,
    shares: Decimal,
    mark_price: Decimal,
) -> None:
    state.open_trade_id = trade_id
    state.position = OpenPosition(
        position_id=position_id,
        security_id=security_id,
        ticker=ticker,
        entry_date=entry_date,
        entry_price=entry_price,
        entry_commission=entry_commission,
        shares=shares,
        highest_price_since_entry=mark_price,
        lowest_price_since_entry=mark_price,
    )
    state.trades.append(
        Trade(
            trade_id=trade_id,
            security_id=security_id,
            ticker=ticker,
            entry_date=entry_date,
            entry_price=entry_price,
            shares=shares,
        )
    )


def close_trade(
    state: PortfolioState,
    exit_date: date,
    exit_price: Decimal,
    gross_pnl: Decimal,
    net_pnl: Decimal,
) -> Trade:
    if state.open_trade_id is None or state.position is None:
        raise ValueError("No open trade to close")

    trade = next(trade for trade in state.trades if trade.trade_id == state.open_trade_id)
    trade.exit_date = exit_date
    trade.exit_price = exit_price
    trade.gross_pnl = gross_pnl
    trade.net_pnl = net_pnl
    trade.holding_days = (exit_date - trade.entry_date).days

    state.position = None
    state.open_trade_id = None
    state.pending_order = None
    return trade


def update_position_marks(state: PortfolioState, mark_price: Decimal) -> None:
    if state.position is None:
        return
    position = state.position
    state.position = position.model_copy(
        update={
            "highest_price_since_entry": max(position.highest_price_since_entry, mark_price),
            "lowest_price_since_entry": min(position.lowest_price_since_entry, mark_price),
        }
    )


def apply_split(state: PortfolioState, ratio: Decimal) -> None:
    if state.position is None or ratio <= Decimal("0"):
        return
    position = state.position
    adjusted_shares = position.shares * ratio
    adjusted_entry = position.entry_price / ratio
    state.position = position.model_copy(
        update={
            "shares": adjusted_shares,
            "entry_price": adjusted_entry,
        }
    )
    if state.open_trade_id is not None:
        for index, trade in enumerate(state.trades):
            if trade.trade_id == state.open_trade_id:
                state.trades[index] = trade.model_copy(
                    update={
                        "shares": adjusted_shares,
                        "entry_price": adjusted_entry,
                    }
                )
                break
