"""Build exit robustness sample-stability inputs from canonical IS/OOS split."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from core.enums import SamplePeriod
from reporting.experiment_aggregators import aggregate_trade_metrics
from research.sample_split import SampleSplit, filter_trades_by_period
from schemas.exit_robustness import ExitSamplePeriodMetrics, ExitSampleStabilityInput
from schemas.results import TradeRecord


def _average_return_pct(trades: Sequence[TradeRecord]) -> Decimal:
    closed = [trade for trade in trades if trade.exit_date is not None]
    if not closed:
        return Decimal("0")

    returns: list[Decimal] = []
    for trade in closed:
        if trade.return_pct is not None:
            returns.append(trade.return_pct)
            continue
        if (
            trade.net_pnl is not None
            and trade.entry_price > Decimal("0")
            and trade.shares > Decimal("0")
        ):
            cost_basis = trade.entry_price * trade.shares
            returns.append(trade.net_pnl / cost_basis)

    if not returns:
        return Decimal("0")
    return sum(returns, start=Decimal("0")) / Decimal(len(returns))


def build_exit_sample_stability_from_split(
    trades: Sequence[TradeRecord],
    *,
    split: SampleSplit,
) -> ExitSampleStabilityInput:
    """Build canonical IS/OOS exit sample stability inputs from closed trades."""
    periods: list[ExitSamplePeriodMetrics] = []
    for sample_period in (SamplePeriod.IN_SAMPLE, SamplePeriod.OUT_OF_SAMPLE):
        filtered = filter_trades_by_period(
            trades,
            split=split,
            sample_period=sample_period,
        )
        _, win_rate, profit_factor, _, _ = aggregate_trade_metrics(filtered)
        periods.append(
            ExitSamplePeriodMetrics(
                period_name=sample_period.value,
                average_return=_average_return_pct(filtered),
                win_rate=win_rate or Decimal("0"),
                profit_factor=profit_factor or Decimal("0"),
            )
        )

    return ExitSampleStabilityInput(periods=periods)
