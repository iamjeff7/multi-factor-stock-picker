"""IC sample-period analysis tests."""

from datetime import date
from decimal import Decimal

import pytest
from tests.factors.ic.conftest import make_forward_return

from core.enums import SamplePeriod
from core.types import SignalId
from factors.ic.calculator import SpearmanICCalculator
from factors.ic.config import ICConfig
from factors.ic.sample_analysis import analyze_ic_by_sample, compute_ic_degradation
from research.sample_split import compute_sample_split
from schemas.ic import DailyICResult, ICSummary


def _daily_ic(evaluation_date: date, ic: Decimal) -> DailyICResult:
    return DailyICResult(
        evaluation_date=evaluation_date,
        signal_id=SignalId("momentum_12m"),
        horizon=21,
        security_count=30,
        ic=ic,
    )


def test_analyze_ic_by_sample_splits_on_trading_days() -> None:
    trading_days = [date(2020, 1, d) for d in range(2, 12)]
    split = compute_sample_split(
        trading_days,
        calendar_start=date(2020, 1, 2),
        calendar_end=date(2020, 1, 11),
    )
    daily_results = [
        _daily_ic(date(2020, 1, 2), Decimal("0.10")),
        _daily_ic(date(2020, 1, 3), Decimal("0.08")),
        _daily_ic(date(2020, 1, 10), Decimal("-0.02")),
        _daily_ic(date(2020, 1, 11), Decimal("-0.04")),
    ]

    analysis = analyze_ic_by_sample(
        daily_results,
        split=split,
        signal_id=SignalId("momentum_12m"),
        horizon=21,
    )

    assert analysis.in_sample_summary.sample_period is SamplePeriod.IN_SAMPLE
    assert analysis.out_of_sample_summary.sample_period is SamplePeriod.OUT_OF_SAMPLE
    assert analysis.in_sample_summary.observation_count == 2
    assert analysis.out_of_sample_summary.observation_count == 2
    assert analysis.in_sample_summary.mean_ic == Decimal("0.09")
    assert analysis.out_of_sample_summary.mean_ic == Decimal("-0.03")
    assert analysis.degradation.is_to_oos_mean_ic_delta == Decimal("-0.12")


def test_compute_ic_degradation_flags_overfitting() -> None:
    is_summary = ICSummary(
        signal_id=SignalId("momentum_12m"),
        horizon=21,
        sample_period=SamplePeriod.IN_SAMPLE,
        mean_ic=Decimal("0.10"),
        median_ic=Decimal("0.09"),
        std_ic=Decimal("0.02"),
        ic_information_ratio=Decimal("5"),
        hit_rate=Decimal("0.75"),
        t_statistic=None,
        p_value=None,
        observation_count=20,
    )
    oos_summary = is_summary.model_copy(
        update={
            "sample_period": SamplePeriod.OUT_OF_SAMPLE,
            "mean_ic": Decimal("0.02"),
            "hit_rate": Decimal("0.52"),
        }
    )

    degradation = compute_ic_degradation(is_summary, oos_summary)

    assert degradation.overfitting_warning is True


def test_calculator_analyze_by_sample() -> None:
    trading_days = [date(2020, 1, d) for d in range(2, 12)]
    split = compute_sample_split(
        trading_days,
        calendar_start=date(2020, 1, 2),
        calendar_end=date(2020, 1, 11),
    )
    daily_results = [
        _daily_ic(date(2020, 1, 2), Decimal("0.10")),
        _daily_ic(date(2020, 1, 10), Decimal("0.04")),
        _daily_ic(date(2020, 1, 11), Decimal("-0.01")),
    ]
    calculator = SpearmanICCalculator(config=ICConfig(minimum_security_count=1))

    analysis = calculator.analyze_by_sample(
        daily_results,
        split=split,
        signal_id=SignalId("momentum_12m"),
        horizon=21,
    )

    assert analysis.in_sample_summary.observation_count == 1
    assert analysis.out_of_sample_summary.observation_count == 2


def test_analyze_ic_by_sample_requires_both_periods() -> None:
    trading_days = [date(2020, 1, d) for d in range(2, 12)]
    split = compute_sample_split(
        trading_days,
        calendar_start=date(2020, 1, 2),
        calendar_end=date(2020, 1, 11),
    )
    daily_results = [_daily_ic(date(2020, 1, 2), Decimal("0.10"))]

    with pytest.raises(ValueError, match="Both IS and OOS IC summaries"):
        analyze_ic_by_sample(
            daily_results,
            split=split,
            signal_id=SignalId("momentum_12m"),
            horizon=21,
        )


def test_build_sample_stability_from_split() -> None:
    from evaluation.robustness.sample_inputs import build_sample_stability_from_split

    trading_days = [date(2020, 1, d) for d in range(2, 12)]
    split = compute_sample_split(
        trading_days,
        calendar_start=date(2020, 1, 2),
        calendar_end=date(2020, 1, 11),
    )
    daily_results = [
        _daily_ic(date(2020, 1, 2), Decimal("0.10")),
        _daily_ic(date(2020, 1, 3), Decimal("0.08")),
        _daily_ic(date(2020, 1, 10), Decimal("-0.02")),
        _daily_ic(date(2020, 1, 11), Decimal("-0.04")),
    ]
    forward_returns = [
        make_forward_return(
            security_id="AAPL",
            forward_return=Decimal("0.05"),
            evaluation_date=date(2020, 1, 2),
        ),
        make_forward_return(
            security_id="AAPL",
            forward_return=Decimal("0.04"),
            evaluation_date=date(2020, 1, 3),
        ),
        make_forward_return(
            security_id="AAPL",
            forward_return=Decimal("-0.01"),
            evaluation_date=date(2020, 1, 10),
        ),
        make_forward_return(
            security_id="AAPL",
            forward_return=Decimal("-0.02"),
            evaluation_date=date(2020, 1, 11),
        ),
    ]

    sample_input = build_sample_stability_from_split(
        daily_results,
        forward_returns,
        split=split,
        signal_id=SignalId("momentum_12m"),
        horizon=21,
    )

    assert len(sample_input.periods) == 2
    assert sample_input.periods[0].period_name == SamplePeriod.IN_SAMPLE.value
    assert sample_input.periods[1].period_name == SamplePeriod.OUT_OF_SAMPLE.value
    assert sample_input.periods[0].mean_ic == Decimal("0.09")
    assert sample_input.periods[1].mean_forward_return == Decimal("-0.015")
