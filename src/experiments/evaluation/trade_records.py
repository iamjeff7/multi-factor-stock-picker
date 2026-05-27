"""Convert simulated trades into persisted trade records."""

from __future__ import annotations

from core.types import ExperimentId
from schemas.backtest import Trade
from schemas.results import TradeRecord


def trades_to_records(
    trades: list[Trade],
    *,
    experiment_id: ExperimentId,
) -> list[TradeRecord]:
    return [
        TradeRecord(
            experiment_id=experiment_id,
            trade_id=trade.trade_id,
            security_id=trade.security_id,
            ticker=trade.ticker,
            entry_date=trade.entry_date,
            entry_price=trade.entry_price,
            exit_date=trade.exit_date,
            exit_price=trade.exit_price,
            shares=trade.shares,
            gross_pnl=trade.gross_pnl,
            net_pnl=trade.net_pnl,
            holding_days=trade.holding_days,
        )
        for trade in trades
    ]
