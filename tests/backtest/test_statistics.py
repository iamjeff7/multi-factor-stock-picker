"""Performance statistics tests."""

from datetime import date
from decimal import Decimal

from backtest.statistics import DefaultPerformanceCalculator
from core.types import SecurityId, Ticker, TradeId
from schemas.backtest import EquityCurvePoint, Trade


def test_performance_calculator_computes_total_return() -> None:
    calculator = DefaultPerformanceCalculator()
    equity_curve = [
        EquityCurvePoint(date=date(2020, 1, 1), portfolio_value=Decimal("10000")),
        EquityCurvePoint(date=date(2020, 1, 2), portfolio_value=Decimal("11000")),
    ]
    trades = [
        Trade(
            trade_id=TradeId("t1"),
            security_id=SecurityId("SEC_TEST"),
            ticker=Ticker("TEST"),
            entry_date=date(2020, 1, 1),
            entry_price=Decimal("100"),
            exit_date=date(2020, 1, 2),
            exit_price=Decimal("110"),
            shares=Decimal("10"),
            gross_pnl=Decimal("100"),
            net_pnl=Decimal("100"),
            holding_days=1,
        )
    ]
    summary = calculator.summarize(trades, equity_curve, Decimal("10000"))
    assert summary.total_return == Decimal("0.1")
    assert summary.number_of_trades == 1
    assert summary.win_rate == Decimal("1")
