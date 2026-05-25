"""Optional cross-sectional preprocessing before ranking."""

from __future__ import annotations

from decimal import Decimal

from factors.scoring.config import WinsorizeConfig
from factors.scoring.ranking import RankObservation


def winsorize_observations(
    observations: list[RankObservation],
    config: WinsorizeConfig,
) -> list[RankObservation]:
    """Clip raw values to configured cross-sectional percentiles."""
    if not observations:
        return []

    sorted_values = sorted(observation.raw_value for observation in observations)
    lower_bound = _percentile_value(sorted_values, config.lower_pct)
    upper_bound = _percentile_value(sorted_values, config.upper_pct)

    return [
        RankObservation(
            security_id=observation.security_id,
            raw_value=_clip(observation.raw_value, lower_bound, upper_bound),
        )
        for observation in observations
    ]


def _percentile_value(sorted_values: list[Decimal], percentile: Decimal) -> Decimal:
    if len(sorted_values) == 1:
        return sorted_values[0]

    position = percentile * Decimal(len(sorted_values) - 1)
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    weight = position - Decimal(lower_index)
    lower_value = sorted_values[lower_index]
    upper_value = sorted_values[upper_index]
    return lower_value + (upper_value - lower_value) * weight


def _clip(value: Decimal, lower_bound: Decimal, upper_bound: Decimal) -> Decimal:
    if value < lower_bound:
        return lower_bound
    if value > upper_bound:
        return upper_bound
    return value
