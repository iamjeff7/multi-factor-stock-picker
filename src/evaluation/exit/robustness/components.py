"""Exit robustness dimension component scorers."""

from __future__ import annotations

from decimal import Decimal

from evaluation.exit.robustness.config import ExitRobustnessConfig
from evaluation.robustness.normalize import (
    average,
    clamp,
    dispersion_penalty,
    normalize_linear,
    normalized_spread,
)
from schemas.exit_robustness import (
    ExitParameterStabilityInput,
    ExitRegimeStabilityInput,
    ExitSampleStabilityInput,
    HoldingPeriodStabilityInput,
    PerformanceStabilityInput,
    RiskStabilityInput,
    TradeDistributionStabilityInput,
)


def score_performance_stability(
    inputs: PerformanceStabilityInput,
    *,
    config: ExitRobustnessConfig,
) -> Decimal:
    mean_score = normalize_linear(
        inputs.average_trade_return,
        floor=config.return_level_floor,
        ceiling=config.return_level_ceiling,
    )
    median_score = normalize_linear(
        inputs.median_trade_return,
        floor=config.return_level_floor,
        ceiling=config.return_level_ceiling,
    )
    win_score = clamp(inputs.win_rate, Decimal("0"), Decimal("1"))
    profit_factor_score = normalize_linear(
        inputs.profit_factor,
        floor=config.profit_factor_floor,
        ceiling=config.profit_factor_ceiling,
    )
    expectancy_score = normalize_linear(
        inputs.expectancy,
        floor=config.expectancy_floor,
        ceiling=config.expectancy_ceiling,
    )
    std_value = inputs.return_volatility or Decimal("0")
    volatility_score = Decimal("1") - clamp(
        std_value / config.return_std_ceiling,
        Decimal("0"),
        Decimal("1"),
    )
    return average(
        [mean_score, median_score, win_score, profit_factor_score, expectancy_score, volatility_score]
    )


def score_regime_stability(
    inputs: ExitRegimeStabilityInput,
    *,
    config: ExitRobustnessConfig,
) -> Decimal:
    if not inputs.regimes:
        return Decimal("0")

    regime_scores = [
        average(
            [
                normalize_linear(
                    regime.average_trade_return,
                    floor=config.return_level_floor,
                    ceiling=config.return_level_ceiling,
                ),
                clamp(regime.win_rate, Decimal("0"), Decimal("1")),
                normalize_linear(
                    regime.profit_factor,
                    floor=config.profit_factor_floor,
                    ceiling=config.profit_factor_ceiling,
                ),
                normalize_linear(
                    regime.expectancy,
                    floor=config.expectancy_floor,
                    ceiling=config.expectancy_ceiling,
                ),
            ]
        )
        for regime in inputs.regimes
    ]
    mean_regime_score = average(regime_scores)
    consistency_score = dispersion_penalty(regime_scores, ceiling=Decimal("0.25"))
    return average([mean_regime_score, consistency_score])


def score_parameter_stability(
    inputs: ExitParameterStabilityInput,
    *,
    config: ExitRobustnessConfig,
) -> Decimal:
    if not inputs.performances:
        return Decimal("0")
    if len(inputs.performances) == 1:
        return normalize_linear(
            inputs.performances[0],
            floor=config.return_level_floor,
            ceiling=config.return_level_ceiling,
        )

    normalized_performances = [
        normalize_linear(
            performance,
            floor=config.return_level_floor,
            ceiling=config.return_level_ceiling,
        )
        for performance in inputs.performances
    ]
    mean_score = average(normalized_performances)
    dispersion_score = dispersion_penalty(normalized_performances, ceiling=Decimal("0.30"))
    baseline = normalized_performances[0]
    worst_drop = max(baseline - performance for performance in normalized_performances)
    sensitivity_score = Decimal("1") - clamp(worst_drop, Decimal("0"), Decimal("1"))
    return average([mean_score, dispersion_score, sensitivity_score])


def score_holding_period_stability(
    inputs: HoldingPeriodStabilityInput,
    *,
    config: ExitRobustnessConfig,
) -> Decimal:
    if not inputs.buckets:
        return Decimal("0")

    bucket_scores = [
        average(
            [
                normalize_linear(
                    bucket.average_return,
                    floor=config.return_level_floor,
                    ceiling=config.return_level_ceiling,
                ),
                clamp(bucket.win_rate, Decimal("0"), Decimal("1")),
                normalize_linear(
                    bucket.profit_factor,
                    floor=config.profit_factor_floor,
                    ceiling=config.profit_factor_ceiling,
                ),
            ]
        )
        for bucket in inputs.buckets
    ]
    if len(bucket_scores) == 1:
        return bucket_scores[0]

    mean_score = average(bucket_scores)
    minimum_score = min(bucket_scores)
    breadth_ratio = minimum_score / mean_score if mean_score > Decimal("0") else Decimal("0")
    dispersion_score = dispersion_penalty(bucket_scores, ceiling=Decimal("0.30"))
    return average([mean_score, breadth_ratio, dispersion_score])


def score_sample_stability(
    inputs: ExitSampleStabilityInput,
    *,
    config: ExitRobustnessConfig,
) -> Decimal:
    if not inputs.periods:
        return Decimal("0")

    return_values = [
        normalize_linear(
            period.average_return,
            floor=config.return_level_floor,
            ceiling=config.return_level_ceiling,
        )
        for period in inputs.periods
    ]
    win_values = [period.win_rate for period in inputs.periods]
    profit_factor_values = [
        normalize_linear(
            period.profit_factor,
            floor=config.profit_factor_floor,
            ceiling=config.profit_factor_ceiling,
        )
        for period in inputs.periods
    ]

    return_consistency = Decimal("1") - normalized_spread(return_values)
    win_consistency = Decimal("1") - normalized_spread(win_values)
    profit_factor_consistency = Decimal("1") - normalized_spread(profit_factor_values)
    return average([return_consistency, win_consistency, profit_factor_consistency])


def score_trade_distribution_stability(
    inputs: TradeDistributionStabilityInput,
    *,
    config: ExitRobustnessConfig,
) -> Decimal:
    breadth_score = clamp(inputs.profitable_trade_pct, Decimal("0"), Decimal("1"))
    concentration_penalty = Decimal("1") - clamp(
        inputs.contribution_concentration / config.concentration_ceiling,
        Decimal("0"),
        Decimal("1"),
    )
    top_trade_penalty = Decimal("1") - clamp(
        inputs.top_trade_contribution_ratio,
        Decimal("0"),
        Decimal("1"),
    )
    largest_winner_penalty = Decimal("1") - clamp(
        inputs.largest_winner_contribution,
        Decimal("0"),
        Decimal("1"),
    )
    return average(
        [breadth_score, concentration_penalty, top_trade_penalty, largest_winner_penalty]
    )


def score_risk_stability(
    inputs: RiskStabilityInput,
    *,
    config: ExitRobustnessConfig,
) -> Decimal:
    drawdown_score = Decimal("1") - clamp(
        abs(inputs.max_drawdown) / config.max_drawdown_ceiling,
        Decimal("0"),
        Decimal("1"),
    )
    volatility_value = inputs.volatility or Decimal("0")
    volatility_score = Decimal("1") - clamp(
        volatility_value / config.volatility_ceiling,
        Decimal("0"),
        Decimal("1"),
    )
    tail_value = inputs.tail_risk or Decimal("0")
    tail_score = Decimal("1") - clamp(
        abs(tail_value) / config.tail_risk_ceiling,
        Decimal("0"),
        Decimal("1"),
    )
    loss_std_value = inputs.trade_loss_std or Decimal("0")
    loss_distribution_score = Decimal("1") - clamp(
        loss_std_value / config.volatility_ceiling,
        Decimal("0"),
        Decimal("1"),
    )
    return average([drawdown_score, volatility_score, tail_score, loss_distribution_score])
