"""IC aggregate statistics tests."""

from datetime import date
from decimal import Decimal

from core.types import SignalId
from factors.ic.aggregates import summarize_ic_series
from schemas.ic import DailyICResult


def test_summarize_ic_series() -> None:
    daily_results = [
        DailyICResult(
            evaluation_date=date(2020, 1, 31),
            signal_id=SignalId("momentum_12m"),
            horizon=21,
            security_count=30,
            ic=Decimal("0.10"),
        ),
        DailyICResult(
            evaluation_date=date(2020, 2, 29),
            signal_id=SignalId("momentum_12m"),
            horizon=21,
            security_count=30,
            ic=Decimal("-0.02"),
        ),
        DailyICResult(
            evaluation_date=date(2020, 3, 31),
            signal_id=SignalId("momentum_12m"),
            horizon=21,
            security_count=30,
            ic=Decimal("0.06"),
        ),
    ]

    summary = summarize_ic_series(
        daily_results,
        signal_id=SignalId("momentum_12m"),
        horizon=21,
    )

    assert summary.mean_ic == Decimal("0.14") / Decimal("3")
    assert summary.median_ic == Decimal("0.06")
    assert summary.hit_rate == Decimal("2") / Decimal("3")
    assert summary.observation_count == 3
    assert summary.std_ic is not None
    assert summary.ic_information_ratio is not None
    assert summary.t_statistic is not None
    assert summary.p_value is not None
