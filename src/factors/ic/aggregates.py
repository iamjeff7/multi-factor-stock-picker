"""Aggregate IC statistics."""

from __future__ import annotations

import math
from collections.abc import Sequence
from decimal import Decimal

from core.enums import SamplePeriod
from core.types import SignalId
from schemas.ic import DailyICResult, ForwardReturn, ICSummary


def summarize_ic_series(
    daily_results: Sequence[DailyICResult],
    *,
    signal_id: SignalId,
    horizon: int,
) -> ICSummary:
    """Compute aggregate IC metrics for a daily IC time series."""
    if not daily_results:
        raise ValueError("At least one daily IC observation is required")

    values = sorted((result.ic for result in daily_results), key=lambda value: value)
    observation_count = len(values)
    mean_ic = sum(values, start=Decimal("0")) / Decimal(observation_count)
    median_ic = _median(values)
    std_ic = _sample_std(values, mean_ic)
    ic_information_ratio = mean_ic / std_ic if std_ic not in (None, Decimal("0")) else None
    hit_rate = Decimal(
        sum(1 for value in values if value > Decimal("0"))
    ) / Decimal(observation_count)
    t_statistic, p_value = _t_test_mean(values, mean_ic, std_ic)

    return ICSummary(
        signal_id=signal_id,
        horizon=horizon,
        sample_period=SamplePeriod.FULL,
        mean_ic=mean_ic,
        median_ic=median_ic,
        std_ic=std_ic,
        ic_information_ratio=ic_information_ratio,
        hit_rate=hit_rate,
        t_statistic=t_statistic,
        p_value=p_value,
        observation_count=observation_count,
    )


def summarize_forward_returns(
    forward_returns: Sequence[ForwardReturn],
    *,
    horizon: int,
) -> tuple[Decimal | None, Decimal | None]:
    """Return mean forward return and positive observation ratio."""
    values = [row.forward_return for row in forward_returns if row.horizon == horizon]
    if not values:
        return None, None
    mean_value = sum(values, start=Decimal("0")) / Decimal(len(values))
    positive_ratio = Decimal(sum(1 for value in values if value > Decimal("0"))) / Decimal(
        len(values)
    )
    return mean_value, positive_ratio


def _median(values: list[Decimal]) -> Decimal:
    midpoint = len(values) // 2
    if len(values) % 2 == 1:
        return values[midpoint]
    return (values[midpoint - 1] + values[midpoint]) / Decimal("2")


def _sample_std(values: list[Decimal], mean_value: Decimal) -> Decimal | None:
    if len(values) < 2:
        return None
    variance = sum((value - mean_value) ** 2 for value in values) / Decimal(len(values) - 1)
    return variance.sqrt()


def _t_test_mean(
    values: list[Decimal],
    mean_value: Decimal,
    std_value: Decimal | None,
) -> tuple[Decimal | None, Decimal | None]:
    if std_value in (None, Decimal("0")) or len(values) < 2:
        return None, None

    t_stat = mean_value / (std_value / Decimal(len(values)).sqrt())
    p_value = _two_sided_normal_p_value(float(t_stat))
    return t_stat, Decimal(str(p_value))


def _two_sided_normal_p_value(t_stat: float) -> float:
    z = abs(t_stat)
    one_tailed = 0.5 * math.erfc(z / math.sqrt(2.0))
    return min(1.0, 2.0 * one_tailed)
