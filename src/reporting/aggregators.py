"""Derived result aggregations."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from decimal import Decimal

from core.types import SecurityId, Ticker
from schemas.results import StockSummaryRecord, TradeRecord


def aggregate_stock_summaries(trades: Sequence[TradeRecord]) -> list[StockSummaryRecord]:
    """Build per-security trade summaries from persisted trade records."""
    if not trades:
        return []

    grouped: dict[tuple[str, str, str], list[TradeRecord]] = defaultdict(list)
    for trade in trades:
        key = (str(trade.experiment_id), str(trade.security_id), str(trade.ticker))
        grouped[key].append(trade)

    summaries: list[StockSummaryRecord] = []
    for (experiment_id, security_id, ticker), security_trades in grouped.items():
        closed = [trade for trade in security_trades if trade.exit_date is not None]
        open_trades = [trade for trade in security_trades if trade.exit_date is None]

        total_gross_pnl = _sum_optional(trade.gross_pnl for trade in security_trades)
        total_net_pnl = _sum_optional(trade.net_pnl for trade in security_trades)
        win_rate, profit_factor = _win_metrics(closed)
        average_return_pct = _average_return_pct(closed)
        average_holding_days = _average_holding_days(closed)
        best_trade_pnl, worst_trade_pnl = _best_worst_pnl(closed)

        summaries.append(
            StockSummaryRecord(
                experiment_id=security_trades[0].experiment_id,
                security_id=SecurityId(security_id),
                ticker=Ticker(ticker),
                number_of_trades=len(security_trades),
                closed_trades=len(closed),
                open_trades=len(open_trades),
                total_gross_pnl=total_gross_pnl,
                total_net_pnl=total_net_pnl,
                average_return_pct=average_return_pct,
                win_rate=win_rate,
                profit_factor=profit_factor,
                average_holding_days=average_holding_days,
                best_trade_pnl=best_trade_pnl,
                worst_trade_pnl=worst_trade_pnl,
            )
        )

    return summaries


def _sum_optional(values: Iterable[Decimal | None]) -> Decimal | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return sum(present, Decimal("0"))


def _win_metrics(
    closed_trades: Sequence[TradeRecord],
) -> tuple[Decimal | None, Decimal | None]:
    if not closed_trades:
        return None, None

    winners = [trade for trade in closed_trades if (trade.net_pnl or Decimal("0")) > 0]
    win_rate = Decimal(str(len(winners) / len(closed_trades)))

    gross_wins = sum(
        ((trade.net_pnl or Decimal("0")) for trade in winners),
        Decimal("0"),
    )
    losers = [trade for trade in closed_trades if (trade.net_pnl or Decimal("0")) < 0]
    gross_losses = abs(
        sum(((trade.net_pnl or Decimal("0")) for trade in losers), Decimal("0"))
    )
    profit_factor = None if gross_losses == 0 else gross_wins / gross_losses
    return win_rate, profit_factor


def _average_return_pct(closed_trades: Sequence[TradeRecord]) -> Decimal | None:
    returns = [trade.return_pct for trade in closed_trades if trade.return_pct is not None]
    if not returns:
        return None
    return sum(returns, Decimal("0")) / Decimal(str(len(returns)))


def _average_holding_days(closed_trades: Sequence[TradeRecord]) -> Decimal | None:
    holding_days = [
        trade.holding_days for trade in closed_trades if trade.holding_days is not None
    ]
    if not holding_days:
        return None
    return Decimal(str(sum(holding_days))) / Decimal(str(len(holding_days)))


def _best_worst_pnl(
    closed_trades: Sequence[TradeRecord],
) -> tuple[Decimal | None, Decimal | None]:
    pnls = [trade.net_pnl for trade in closed_trades if trade.net_pnl is not None]
    if not pnls:
        return None, None
    return max(pnls), min(pnls)
