"""Build entry robustness sample-stability inputs from canonical IS/OOS split."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from core.enums import SamplePeriod
from core.types import SignalId
from factors.ic.aggregates import summarize_forward_returns
from factors.ic.sample_analysis import (
    analyze_ic_by_sample,
    filter_forward_returns_by_period,
)
from research.sample_split import SampleSplit
from schemas.ic import DailyICResult, ForwardReturn, ICSampleAnalysis
from schemas.robustness import SamplePeriodMetrics, SampleStabilityInput


def build_sample_stability_input(
    *,
    is_mean_ic: Decimal,
    oos_mean_ic: Decimal,
    is_mean_forward_return: Decimal,
    oos_mean_forward_return: Decimal,
    is_hit_rate: Decimal,
    oos_hit_rate: Decimal,
) -> SampleStabilityInput:
    """Build canonical IS/OOS sample stability inputs."""
    return SampleStabilityInput(
        periods=[
            SamplePeriodMetrics(
                period_name=SamplePeriod.IN_SAMPLE.value,
                mean_ic=is_mean_ic,
                mean_forward_return=is_mean_forward_return,
                hit_rate=is_hit_rate,
            ),
            SamplePeriodMetrics(
                period_name=SamplePeriod.OUT_OF_SAMPLE.value,
                mean_ic=oos_mean_ic,
                mean_forward_return=oos_mean_forward_return,
                hit_rate=oos_hit_rate,
            ),
        ]
    )


def build_sample_stability_from_ic_analysis(
    analysis: ICSampleAnalysis,
    forward_returns: Sequence[ForwardReturn],
    *,
    split: SampleSplit,
) -> SampleStabilityInput:
    is_forward_returns = filter_forward_returns_by_period(
        forward_returns,
        split=split,
        sample_period=SamplePeriod.IN_SAMPLE,
        horizon=analysis.horizon,
    )
    oos_forward_returns = filter_forward_returns_by_period(
        forward_returns,
        split=split,
        sample_period=SamplePeriod.OUT_OF_SAMPLE,
        horizon=analysis.horizon,
    )
    is_mean_forward_return, _ = summarize_forward_returns(
        is_forward_returns,
        horizon=analysis.horizon,
    )
    oos_mean_forward_return, _ = summarize_forward_returns(
        oos_forward_returns,
        horizon=analysis.horizon,
    )
    if is_mean_forward_return is None or oos_mean_forward_return is None:
        raise ValueError("Forward returns are required in both IS and OOS periods")

    return build_sample_stability_input(
        is_mean_ic=analysis.in_sample_summary.mean_ic,
        oos_mean_ic=analysis.out_of_sample_summary.mean_ic,
        is_mean_forward_return=is_mean_forward_return,
        oos_mean_forward_return=oos_mean_forward_return,
        is_hit_rate=analysis.in_sample_summary.hit_rate,
        oos_hit_rate=analysis.out_of_sample_summary.hit_rate,
    )


def build_sample_stability_from_split(
    daily_results: Sequence[DailyICResult],
    forward_returns: Sequence[ForwardReturn],
    *,
    split: SampleSplit,
    signal_id: SignalId,
    horizon: int,
) -> SampleStabilityInput:
    analysis = analyze_ic_by_sample(
        daily_results,
        split=split,
        signal_id=signal_id,
        horizon=horizon,
    )
    return build_sample_stability_from_ic_analysis(
        analysis,
        forward_returns,
        split=split,
    )
