"""Robustness dimension component scorers."""

from __future__ import annotations

from decimal import Decimal

from evaluation.robustness.config import EntryRobustnessConfig
from evaluation.robustness.normalize import (
    average,
    clamp,
    dispersion_penalty,
    normalize_linear,
    normalized_spread,
)
from schemas.robustness import (
    BreadthStabilityInput,
    ICStabilityInput,
    ParameterStabilityInput,
    RankStabilityInput,
    RegimeStabilityInput,
    ReturnStabilityInput,
    SampleStabilityInput,
)


def score_ic_stability(
    inputs: ICStabilityInput,
    *,
    config: EntryRobustnessConfig,
) -> Decimal:
    mean_score = normalize_linear(
        inputs.mean_ic,
        floor=config.ic_level_floor,
        ceiling=config.ic_level_ceiling,
    )
    median_score = normalize_linear(
        inputs.median_ic,
        floor=config.ic_level_floor,
        ceiling=config.ic_level_ceiling,
    )
    hit_score = clamp(inputs.hit_rate, Decimal("0"), Decimal("1"))
    std_value = inputs.std_ic or Decimal("0")
    volatility_score = Decimal("1") - clamp(
        std_value / config.ic_std_ceiling,
        Decimal("0"),
        Decimal("1"),
    )
    ir_value = inputs.ic_information_ratio or Decimal("0")
    ir_score = clamp(ir_value / config.ic_ir_ceiling, Decimal("0"), Decimal("1"))
    return average([mean_score, median_score, hit_score, volatility_score, ir_score])


def score_return_stability(
    inputs: ReturnStabilityInput,
    *,
    config: EntryRobustnessConfig,
) -> Decimal:
    mean_score = normalize_linear(
        inputs.mean_forward_return,
        floor=config.return_level_floor,
        ceiling=config.return_level_ceiling,
    )
    median_score = normalize_linear(
        inputs.median_forward_return,
        floor=config.return_level_floor,
        ceiling=config.return_level_ceiling,
    )
    positive_score = clamp(inputs.positive_period_ratio, Decimal("0"), Decimal("1"))
    std_value = inputs.return_std or Decimal("0")
    volatility_score = Decimal("1") - clamp(
        std_value / config.return_std_ceiling,
        Decimal("0"),
        Decimal("1"),
    )
    return average([mean_score, median_score, positive_score, volatility_score])


def score_regime_stability(
    inputs: RegimeStabilityInput,
    *,
    config: EntryRobustnessConfig,
) -> Decimal:
    if not inputs.regimes:
        return Decimal("0")

    regime_scores = [
        average(
            [
                normalize_linear(
                    regime.mean_ic,
                    floor=config.ic_level_floor,
                    ceiling=config.ic_level_ceiling,
                ),
                normalize_linear(
                    regime.mean_forward_return,
                    floor=config.return_level_floor,
                    ceiling=config.return_level_ceiling,
                ),
                clamp(regime.hit_rate, Decimal("0"), Decimal("1")),
            ]
        )
        for regime in inputs.regimes
    ]
    mean_regime_score = average(regime_scores)
    consistency_score = dispersion_penalty(regime_scores, ceiling=Decimal("0.25"))
    return average([mean_regime_score, consistency_score])


def score_parameter_stability(
    inputs: ParameterStabilityInput,
    *,
    config: EntryRobustnessConfig,
) -> Decimal:
    if not inputs.performances:
        return Decimal("0")
    if len(inputs.performances) == 1:
        return normalize_linear(
            inputs.performances[0],
            floor=config.ic_level_floor,
            ceiling=config.ic_level_ceiling,
        )

    normalized_performances = [
        normalize_linear(
            performance,
            floor=config.ic_level_floor,
            ceiling=config.ic_level_ceiling,
        )
        for performance in inputs.performances
    ]
    mean_score = average(normalized_performances)
    dispersion_score = dispersion_penalty(normalized_performances, ceiling=Decimal("0.30"))
    baseline = normalized_performances[0]
    worst_drop = max(baseline - performance for performance in normalized_performances)
    sensitivity_score = Decimal("1") - clamp(worst_drop, Decimal("0"), Decimal("1"))
    return average([mean_score, dispersion_score, sensitivity_score])


def score_rank_stability(inputs: RankStabilityInput) -> Decimal:
    if inputs.rank_correlations:
        correlation_scores = [
            clamp((correlation + Decimal("1")) / Decimal("2"), Decimal("0"), Decimal("1"))
            for correlation in inputs.rank_correlations
        ]
        correlation_score = average(correlation_scores)
    else:
        correlation_score = Decimal("0")

    persistence_score = clamp(inputs.top_decile_persistence, Decimal("0"), Decimal("1"))
    turnover_score = Decimal("1") - clamp(inputs.turnover_rate, Decimal("0"), Decimal("1"))
    return average([correlation_score, persistence_score, turnover_score])


def score_breadth_stability(
    inputs: BreadthStabilityInput,
    *,
    config: EntryRobustnessConfig,
) -> Decimal:
    if not inputs.performances:
        return Decimal("0")

    normalized = [
        normalize_linear(
            performance,
            floor=config.ic_level_floor,
            ceiling=config.ic_level_ceiling,
        )
        for performance in inputs.performances.values()
    ]
    if len(normalized) == 1:
        return normalized[0]

    mean_score = average(normalized)
    minimum_score = min(normalized)
    breadth_ratio = (
        minimum_score / mean_score if mean_score > Decimal("0") else Decimal("0")
    )
    dispersion_score = dispersion_penalty(normalized, ceiling=Decimal("0.30"))
    return average([mean_score, breadth_ratio, dispersion_score])


def score_sample_stability(
    inputs: SampleStabilityInput,
    *,
    config: EntryRobustnessConfig,
) -> Decimal:
    if not inputs.periods:
        return Decimal("0")

    ic_values = [period.mean_ic for period in inputs.periods]
    return_values = [period.mean_forward_return for period in inputs.periods]
    hit_values = [period.hit_rate for period in inputs.periods]

    ic_consistency = Decimal("1") - normalized_spread(
        [
            normalize_linear(
                value,
                floor=config.ic_level_floor,
                ceiling=config.ic_level_ceiling,
            )
            for value in ic_values
        ]
    )
    return_consistency = Decimal("1") - normalized_spread(
        [
            normalize_linear(
                value,
                floor=config.return_level_floor,
                ceiling=config.return_level_ceiling,
            )
            for value in return_values
        ]
    )
    hit_consistency = Decimal("1") - normalized_spread(hit_values)
    return average([ic_consistency, return_consistency, hit_consistency])
