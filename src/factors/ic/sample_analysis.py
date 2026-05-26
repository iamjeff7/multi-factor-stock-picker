"""In-sample / out-of-sample IC analysis."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from core.enums import SamplePeriod
from core.types import SignalId
from factors.ic.aggregates import summarize_ic_series
from research.sample_split import SampleSplit, classify_date
from schemas.ic import (
    DailyICResult,
    ForwardReturn,
    ICDegradationMetrics,
    ICSampleAnalysis,
    ICSummary,
)


def filter_daily_ic_by_period(
    daily_results: Sequence[DailyICResult],
    *,
    split: SampleSplit,
    sample_period: SamplePeriod,
) -> list[DailyICResult]:
    if sample_period is SamplePeriod.FULL:
        return list(daily_results)
    return [
        result
        for result in daily_results
        if classify_date(result.evaluation_date, split) is sample_period
    ]


def filter_forward_returns_by_period(
    forward_returns: Sequence[ForwardReturn],
    *,
    split: SampleSplit,
    sample_period: SamplePeriod,
    horizon: int,
) -> list[ForwardReturn]:
    if sample_period is SamplePeriod.FULL:
        return [row for row in forward_returns if row.horizon == horizon]
    return [
        row
        for row in forward_returns
        if row.horizon == horizon
        and classify_date(row.evaluation_date, split) is sample_period
    ]


def summarize_ic_for_period(
    daily_results: Sequence[DailyICResult],
    *,
    split: SampleSplit,
    signal_id: SignalId,
    horizon: int,
    sample_period: SamplePeriod,
) -> ICSummary | None:
    filtered = filter_daily_ic_by_period(
        daily_results,
        split=split,
        sample_period=sample_period,
    )
    period_results = [
        result
        for result in filtered
        if result.signal_id == signal_id and result.horizon == horizon
    ]
    if not period_results:
        return None
    summary = summarize_ic_series(
        period_results,
        signal_id=signal_id,
        horizon=horizon,
    )
    return summary.model_copy(update={"sample_period": sample_period})


def compute_ic_degradation(
    is_summary: ICSummary,
    oos_summary: ICSummary,
    *,
    mean_ic_ratio_threshold: Decimal = Decimal("0.5"),
) -> ICDegradationMetrics:
    mean_delta = oos_summary.mean_ic - is_summary.mean_ic
    hit_delta = oos_summary.hit_rate - is_summary.hit_rate

    overfitting_warning = False
    if (
        is_summary.mean_ic > Decimal("0")
        and oos_summary.mean_ic < is_summary.mean_ic * mean_ic_ratio_threshold
    ):
        overfitting_warning = True
    if is_summary.mean_ic > Decimal("0") and oos_summary.mean_ic <= Decimal("0"):
        overfitting_warning = True

    return ICDegradationMetrics(
        is_mean_ic=is_summary.mean_ic,
        oos_mean_ic=oos_summary.mean_ic,
        is_to_oos_mean_ic_delta=mean_delta,
        is_hit_rate=is_summary.hit_rate,
        oos_hit_rate=oos_summary.hit_rate,
        is_to_oos_hit_rate_delta=hit_delta,
        is_ic_information_ratio=is_summary.ic_information_ratio,
        oos_ic_information_ratio=oos_summary.ic_information_ratio,
        overfitting_warning=overfitting_warning,
    )


def analyze_ic_by_sample(
    daily_results: Sequence[DailyICResult],
    *,
    split: SampleSplit,
    signal_id: SignalId,
    horizon: int,
) -> ICSampleAnalysis:
    """Summarize IC separately for IS, OOS, and FULL periods."""
    is_summary = summarize_ic_for_period(
        daily_results,
        split=split,
        signal_id=signal_id,
        horizon=horizon,
        sample_period=SamplePeriod.IN_SAMPLE,
    )
    oos_summary = summarize_ic_for_period(
        daily_results,
        split=split,
        signal_id=signal_id,
        horizon=horizon,
        sample_period=SamplePeriod.OUT_OF_SAMPLE,
    )
    if is_summary is None or oos_summary is None:
        raise ValueError("Both IS and OOS IC summaries require observations in each period")

    full_summary = summarize_ic_for_period(
        daily_results,
        split=split,
        signal_id=signal_id,
        horizon=horizon,
        sample_period=SamplePeriod.FULL,
    )

    return ICSampleAnalysis(
        signal_id=signal_id,
        horizon=horizon,
        full_summary=full_summary,
        in_sample_summary=is_summary,
        out_of_sample_summary=oos_summary,
        degradation=compute_ic_degradation(is_summary, oos_summary),
    )
