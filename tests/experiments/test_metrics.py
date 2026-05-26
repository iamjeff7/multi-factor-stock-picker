"""Tests for experiment metrics."""

from datetime import date
from decimal import Decimal

from core.types import SecurityId, Ticker, TradeId
from experiments.metrics import calendar_months_between, compute_performance_metrics
from schemas.backtest import Trade


def test_calendar_months_between_counts_inclusive_months() -> None:
    assert calendar_months_between(date(2025, 1, 2), date(2025, 12, 31)) == Decimal("12")


def test_compute_performance_metrics_trade_frequency_fields() -> None:
    trades = [
        Trade(
            trade_id=TradeId("t1"),
            security_id=SecurityId("SEC_AAPL"),
            ticker=Ticker("AAPL"),
            entry_date=date(2025, 1, 2),
            entry_price=Decimal("100"),
            exit_date=date(2025, 2, 2),
            exit_price=Decimal("110"),
            shares=Decimal("10"),
            gross_pnl=Decimal("100"),
            net_pnl=Decimal("100"),
            holding_days=31,
        )
    ]
    metrics = compute_performance_metrics(
        trades,
        trading_days=252,
        calendar_start=date(2025, 1, 2),
        calendar_end=date(2025, 12, 31),
        initial_capital=Decimal("10000"),
    )
    assert metrics.round_trips == 1
    assert metrics.trades_per_trading_days == Decimal("1") / Decimal("252")
    assert metrics.trades_per_month == Decimal("1") / Decimal("12")
