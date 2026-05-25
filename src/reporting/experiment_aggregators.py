"""Cross-stock experiment aggregation."""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from decimal import Decimal

from core.enums import SamplePeriod
from core.types import ExperimentId, SecurityId
from schemas.results import ExperimentSummaryRecord, TradeRecord


def aggregate_trade_metrics(
    trades: Sequence[TradeRecord],
) -> tuple[int, Decimal | None, Decimal | None, Decimal | None, Decimal | None]:
    closed = [trade for trade in trades if trade.exit_date is not None]
    if not closed:
        return 0, None, None, None, None

    winners = [trade for trade in closed if (trade.net_pnl or Decimal("0")) > 0]
    win_rate = Decimal(str(len(winners) / len(closed)))

    gross_wins = sum(
        ((trade.net_pnl or Decimal("0")) for trade in winners),
        Decimal("0"),
    )
    losers = [trade for trade in closed if (trade.net_pnl or Decimal("0")) < 0]
    gross_losses = abs(
        sum(((trade.net_pnl or Decimal("0")) for trade in losers), Decimal("0"))
    )
    profit_factor = None if gross_losses == 0 else gross_wins / gross_losses

    average_trade = sum((trade.net_pnl or Decimal("0")) for trade in closed) / Decimal(
        str(len(closed))
    )
    total_net_pnl = sum(
        ((trade.net_pnl or Decimal("0")) for trade in closed),
        Decimal("0"),
    )
    return len(closed), win_rate, profit_factor, average_trade, total_net_pnl


def aggregate_stock_return_stats(
    stock_returns: Sequence[Decimal],
) -> tuple[Decimal | None, Decimal | None, Decimal | None, Decimal | None, Decimal | None]:
    if not stock_returns:
        return None, None, None, None, None

    sorted_returns = sorted(stock_returns)
    mean_return = Decimal(str(statistics.fmean(stock_returns)))
    median_return = Decimal(str(statistics.median(stock_returns)))
    positive = sum(1 for value in stock_returns if value > Decimal("0"))
    pct_positive = Decimal(str(positive / len(stock_returns)))
    return mean_return, median_return, pct_positive, sorted_returns[-1], sorted_returns[0]


def aggregate_stock_returns_from_trades(
    trades: Sequence[TradeRecord],
    *,
    initial_capital: Decimal,
    security_ids: Sequence[SecurityId],
) -> list[Decimal]:
    if initial_capital <= Decimal("0"):
        return []

    grouped: dict[str, Decimal] = {str(security_id): Decimal("0") for security_id in security_ids}
    for trade in trades:
        if trade.exit_date is None or trade.net_pnl is None:
            continue
        grouped[str(trade.security_id)] = grouped.get(str(trade.security_id), Decimal("0")) + (
            trade.net_pnl
        )

    return [pnl / initial_capital for pnl in grouped.values()]


def aggregate_experiment_summary(
    experiment_id: ExperimentId,
    *,
    securities_requested: int,
    securities_completed: int,
    securities_skipped: int,
    stock_returns: Sequence[Decimal],
    trades: Sequence[TradeRecord],
    sample_period: SamplePeriod = SamplePeriod.FULL,
) -> ExperimentSummaryRecord:
    number_of_trades, win_rate, profit_factor, average_trade, total_net_pnl = (
        aggregate_trade_metrics(trades)
    )
    mean_return, median_return, pct_positive, best_return, worst_return = (
        aggregate_stock_return_stats(stock_returns)
    )

    return ExperimentSummaryRecord(
        experiment_id=experiment_id,
        sample_period=sample_period,
        securities_requested=securities_requested,
        securities_completed=securities_completed,
        securities_skipped=securities_skipped,
        mean_stock_return=mean_return,
        median_stock_return=median_return,
        pct_stocks_positive=pct_positive,
        best_stock_return=best_return,
        worst_stock_return=worst_return,
        number_of_trades=number_of_trades,
        win_rate=win_rate,
        profit_factor=profit_factor,
        average_trade=average_trade,
        total_net_pnl=total_net_pnl,
    )
