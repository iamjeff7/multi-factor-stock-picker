"""Aggregate factor performance statistics."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from decimal import Decimal

from core.enums import SamplePeriod
from core.types import SignalId
from factors.ic.spearman import spearman_correlation
from factors.performance.config import FactorPerformanceConfig
from research.sample_split import SampleSplit, classify_date
from schemas.performance import (
    FactorPerformanceSampleAnalysis,
    FactorPerformanceSummary,
    LongShortResult,
    QuantileReturnResult,
    SpreadResult,
)


def summarize_performance(
    *,
    signal_id: SignalId,
    horizon: int,
    quantile_returns: Sequence[QuantileReturnResult],
    spreads: Sequence[SpreadResult],
    long_shorts: Sequence[LongShortResult],
    config: FactorPerformanceConfig,
    sample_period: SamplePeriod = SamplePeriod.FULL,
) -> FactorPerformanceSummary | None:
    if not spreads or not long_shorts:
        return None

    top_quantile = spreads[0].top_quantile
    bottom_quantile = spreads[0].bottom_quantile
    bucket_count = max(
        (row.quantile for row in quantile_returns),
        default=config.quantile_count,
    )

    top_returns = [
        row.average_return
        for row in quantile_returns
        if row.quantile == top_quantile
    ]
    bottom_returns = [
        row.average_return
        for row in quantile_returns
        if row.quantile == bottom_quantile
    ]
    spread_values = [row.spread_return for row in spreads]
    long_short_values = [row.long_short_return for row in long_shorts]

    mean_top_return = _mean(top_returns)
    mean_bottom_return = _mean(bottom_returns)
    mean_spread = _mean(spread_values)
    mean_long_short_return = _mean(long_short_values)
    if (
        mean_top_return is None
        or mean_bottom_return is None
        or mean_spread is None
        or mean_long_short_return is None
    ):
        return None

    spread_win_rate = Decimal(
        sum(1 for value in spread_values if value > Decimal("0"))
    ) / Decimal(len(spread_values))

    return FactorPerformanceSummary(
        signal_id=signal_id,
        horizon=horizon,
        sample_period=sample_period,
        quantile_count=bucket_count,
        top_quantile=top_quantile,
        bottom_quantile=bottom_quantile,
        mean_top_return=mean_top_return,
        mean_bottom_return=mean_bottom_return,
        mean_spread=mean_spread,
        mean_long_short_return=mean_long_short_return,
        spread_win_rate=spread_win_rate,
        monotonicity_correlation=_monotonicity_correlation(quantile_returns),
        observation_count=len(spreads),
    )


def analyze_performance_by_sample(
    *,
    signal_id: SignalId,
    horizon: int,
    quantile_returns: Sequence[QuantileReturnResult],
    spreads: Sequence[SpreadResult],
    long_shorts: Sequence[LongShortResult],
    split: SampleSplit,
    config: FactorPerformanceConfig,
) -> FactorPerformanceSampleAnalysis:
    is_summary = _summarize_for_period(
        signal_id=signal_id,
        horizon=horizon,
        quantile_returns=quantile_returns,
        spreads=spreads,
        long_shorts=long_shorts,
        split=split,
        sample_period=SamplePeriod.IN_SAMPLE,
        config=config,
    )
    oos_summary = _summarize_for_period(
        signal_id=signal_id,
        horizon=horizon,
        quantile_returns=quantile_returns,
        spreads=spreads,
        long_shorts=long_shorts,
        split=split,
        sample_period=SamplePeriod.OUT_OF_SAMPLE,
        config=config,
    )
    if is_summary is None or oos_summary is None:
        raise ValueError(
            "Both IS and OOS performance summaries require observations in each period"
        )

    full_summary = _summarize_for_period(
        signal_id=signal_id,
        horizon=horizon,
        quantile_returns=quantile_returns,
        spreads=spreads,
        long_shorts=long_shorts,
        split=split,
        sample_period=SamplePeriod.FULL,
        config=config,
    )

    return FactorPerformanceSampleAnalysis(
        signal_id=signal_id,
        horizon=horizon,
        full_summary=full_summary,
        in_sample_summary=is_summary,
        out_of_sample_summary=oos_summary,
    )


def _summarize_for_period(
    *,
    signal_id: SignalId,
    horizon: int,
    quantile_returns: Sequence[QuantileReturnResult],
    spreads: Sequence[SpreadResult],
    long_shorts: Sequence[LongShortResult],
    split: SampleSplit,
    sample_period: SamplePeriod,
    config: FactorPerformanceConfig,
) -> FactorPerformanceSummary | None:
    period_quantiles = _filter_quantiles_by_period(quantile_returns, split, sample_period)
    period_spreads = _filter_spreads_by_period(spreads, split, sample_period)
    period_long_shorts = _filter_long_shorts_by_period(long_shorts, split, sample_period)
    return summarize_performance(
        signal_id=signal_id,
        horizon=horizon,
        quantile_returns=period_quantiles,
        spreads=period_spreads,
        long_shorts=period_long_shorts,
        config=config,
        sample_period=sample_period,
    )


def _filter_quantiles_by_period(
    rows: Sequence[QuantileReturnResult],
    split: SampleSplit,
    sample_period: SamplePeriod,
) -> list[QuantileReturnResult]:
    if sample_period is SamplePeriod.FULL:
        return list(rows)
    return [
        row
        for row in rows
        if classify_date(row.evaluation_date, split) is sample_period
    ]


def _filter_spreads_by_period(
    rows: Sequence[SpreadResult],
    split: SampleSplit,
    sample_period: SamplePeriod,
) -> list[SpreadResult]:
    if sample_period is SamplePeriod.FULL:
        return list(rows)
    return [
        row
        for row in rows
        if classify_date(row.evaluation_date, split) is sample_period
    ]


def _filter_long_shorts_by_period(
    rows: Sequence[LongShortResult],
    split: SampleSplit,
    sample_period: SamplePeriod,
) -> list[LongShortResult]:
    if sample_period is SamplePeriod.FULL:
        return list(rows)
    return [
        row
        for row in rows
        if classify_date(row.evaluation_date, split) is sample_period
    ]


def _monotonicity_correlation(
    quantile_returns: Sequence[QuantileReturnResult],
) -> Decimal | None:
    totals: dict[int, list[Decimal]] = defaultdict(list)
    for row in quantile_returns:
        totals[row.quantile].append(row.average_return)

    quantile_numbers = sorted(totals)
    if len(quantile_numbers) < 2:
        return None

    mean_returns = [
        sum(totals[quantile], start=Decimal("0")) / Decimal(len(totals[quantile]))
        for quantile in quantile_numbers
    ]
    try:
        return spearman_correlation(
            [Decimal(value) for value in quantile_numbers],
            mean_returns,
        )
    except ValueError:
        return None


def _mean(values: Sequence[Decimal]) -> Decimal | None:
    if not values:
        return None
    return sum(values, start=Decimal("0")) / Decimal(len(values))
