"""Stock summary aggregation tests."""

from decimal import Decimal

from core.types import TradeId
from reporting.aggregators import aggregate_stock_summaries
from schemas.results import TradeRecord


def test_aggregate_stock_summaries_mixed_trades(sample_trade: TradeRecord) -> None:
    trades = [
        sample_trade,
        sample_trade.model_copy(
            update={
                "trade_id": TradeId("trade_002"),
                "net_pnl": Decimal("-50"),
                "gross_pnl": Decimal("-50"),
            }
        ),
        sample_trade.model_copy(
            update={
                "trade_id": TradeId("trade_003"),
                "net_pnl": None,
                "gross_pnl": None,
                "exit_date": None,
                "exit_price": None,
                "holding_days": None,
                "return_pct": None,
            }
        ),
    ]

    summaries = aggregate_stock_summaries(trades)

    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.number_of_trades == 3
    assert summary.closed_trades == 2
    assert summary.open_trades == 1
    assert summary.win_rate == Decimal("0.5")
    assert summary.total_net_pnl == Decimal("50")
    assert summary.best_trade_pnl == Decimal("100")
    assert summary.worst_trade_pnl == Decimal("-50")


def test_aggregate_stock_summaries_empty() -> None:
    assert aggregate_stock_summaries([]) == []
