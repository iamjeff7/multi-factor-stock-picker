"""Exit robustness sample input builder tests."""

from datetime import date
from decimal import Decimal

from core.enums import SamplePeriod
from core.types import ExperimentId, SecurityId, Ticker, TradeId
from evaluation.exit.robustness.sample_inputs import build_exit_sample_stability_from_split
from research.sample_split import compute_sample_split
from schemas.results import TradeRecord


def test_build_exit_sample_stability_from_split() -> None:
    trading_days = [date(2020, 1, d) for d in range(2, 12)]
    split = compute_sample_split(
        trading_days,
        calendar_start=date(2020, 1, 2),
        calendar_end=date(2020, 1, 11),
    )
    trades = [
        TradeRecord(
            experiment_id=ExperimentId("exp_test"),
            trade_id=TradeId("trade_is"),
            security_id=SecurityId("SEC_AAPL"),
            ticker=Ticker("AAPL"),
            entry_date=date(2020, 1, 2),
            entry_price=Decimal("100"),
            exit_date=date(2020, 1, 3),
            exit_price=Decimal("110"),
            shares=Decimal("10"),
            net_pnl=Decimal("100"),
            return_pct=Decimal("0.10"),
        ),
        TradeRecord(
            experiment_id=ExperimentId("exp_test"),
            trade_id=TradeId("trade_oos"),
            security_id=SecurityId("SEC_AAPL"),
            ticker=Ticker("AAPL"),
            entry_date=date(2020, 1, 10),
            entry_price=Decimal("100"),
            exit_date=date(2020, 1, 11),
            exit_price=Decimal("95"),
            shares=Decimal("10"),
            net_pnl=Decimal("-50"),
            return_pct=Decimal("-0.05"),
        ),
    ]

    sample_input = build_exit_sample_stability_from_split(trades, split=split)

    assert len(sample_input.periods) == 2
    assert sample_input.periods[0].period_name == SamplePeriod.IN_SAMPLE.value
    assert sample_input.periods[1].period_name == SamplePeriod.OUT_OF_SAMPLE.value
    assert sample_input.periods[0].average_return == Decimal("0.10")
    assert sample_input.periods[1].average_return == Decimal("-0.05")
    assert sample_input.periods[0].win_rate == Decimal("1")
    assert sample_input.periods[1].win_rate == Decimal("0")
