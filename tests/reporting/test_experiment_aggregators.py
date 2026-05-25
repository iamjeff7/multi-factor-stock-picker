"""Experiment aggregation tests."""

from decimal import Decimal

from core.types import ExperimentId, TradeId
from reporting.experiment_aggregators import aggregate_experiment_summary


def test_aggregate_experiment_summary_pooled_trades(sample_trade) -> None:
    trades = [
        sample_trade,
        sample_trade.model_copy(
            update={
                "trade_id": TradeId("trade_002"),
                "net_pnl": Decimal("-25"),
                "gross_pnl": Decimal("-25"),
            }
        ),
    ]

    summary = aggregate_experiment_summary(
        ExperimentId("exp_test001"),
        securities_requested=2,
        securities_completed=2,
        securities_skipped=0,
        stock_returns=[Decimal("0.10"), Decimal("-0.05")],
        trades=trades,
    )

    assert summary.securities_requested == 2
    assert summary.number_of_trades == 2
    assert summary.win_rate == Decimal("0.5")
    assert summary.mean_stock_return == Decimal("0.025")
    assert summary.total_net_pnl == Decimal("75")
