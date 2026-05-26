"""Robustness component scorer tests."""

from decimal import Decimal

from core.enums import SamplePeriod
from evaluation.robustness.components import (
    score_breadth_stability,
    score_ic_stability,
    score_parameter_stability,
    score_rank_stability,
    score_regime_stability,
    score_return_stability,
    score_sample_stability,
)
from evaluation.robustness.config import EntryRobustnessConfig
from schemas.robustness import (
    BreadthStabilityInput,
    ICStabilityInput,
    ParameterStabilityInput,
    RankStabilityInput,
    RegimeMetrics,
    RegimeStabilityInput,
    ReturnStabilityInput,
    SamplePeriodMetrics,
    SampleStabilityInput,
)


def test_ic_stability_scores_high_for_strong_ic_metrics() -> None:
    config = EntryRobustnessConfig()
    score = score_ic_stability(
        ICStabilityInput(
            mean_ic=Decimal("0.10"),
            median_ic=Decimal("0.09"),
            std_ic=Decimal("0.02"),
            hit_rate=Decimal("0.80"),
            ic_information_ratio=Decimal("1.5"),
        ),
        config=config,
    )
    assert score > Decimal("0.80")


def test_return_stability_penalizes_high_volatility() -> None:
    config = EntryRobustnessConfig()
    stable = score_return_stability(
        ReturnStabilityInput(
            mean_forward_return=Decimal("0.04"),
            median_forward_return=Decimal("0.04"),
            return_std=Decimal("0.01"),
            positive_period_ratio=Decimal("0.80"),
        ),
        config=config,
    )
    unstable = score_return_stability(
        ReturnStabilityInput(
            mean_forward_return=Decimal("0.04"),
            median_forward_return=Decimal("0.04"),
            return_std=Decimal("0.09"),
            positive_period_ratio=Decimal("0.80"),
        ),
        config=config,
    )
    assert stable > unstable


def test_regime_stability_rewards_consistent_regimes() -> None:
    config = EntryRobustnessConfig()
    consistent = score_regime_stability(
        RegimeStabilityInput(
            regimes=[
                RegimeMetrics(
                    regime_name="bull",
                    mean_ic=Decimal("0.06"),
                    mean_forward_return=Decimal("0.04"),
                    hit_rate=Decimal("0.65"),
                ),
                RegimeMetrics(
                    regime_name="bear",
                    mean_ic=Decimal("0.05"),
                    mean_forward_return=Decimal("0.03"),
                    hit_rate=Decimal("0.60"),
                ),
            ]
        ),
        config=config,
    )
    inconsistent = score_regime_stability(
        RegimeStabilityInput(
            regimes=[
                RegimeMetrics(
                    regime_name="bull",
                    mean_ic=Decimal("0.10"),
                    mean_forward_return=Decimal("0.08"),
                    hit_rate=Decimal("0.80"),
                ),
                RegimeMetrics(
                    regime_name="bear",
                    mean_ic=Decimal("-0.05"),
                    mean_forward_return=Decimal("-0.04"),
                    hit_rate=Decimal("0.30"),
                ),
            ]
        ),
        config=config,
    )
    assert consistent > inconsistent


def test_parameter_stability_penalizes_large_dispersion() -> None:
    config = EntryRobustnessConfig()
    stable = score_parameter_stability(
        ParameterStabilityInput(performances=[Decimal("0.07"), Decimal("0.065"), Decimal("0.06")]),
        config=config,
    )
    unstable = score_parameter_stability(
        ParameterStabilityInput(performances=[Decimal("0.08"), Decimal("0.01"), Decimal("-0.03")]),
        config=config,
    )
    assert stable > unstable


def test_rank_stability_rewards_high_correlation_and_persistence() -> None:
    stable = score_rank_stability(
        RankStabilityInput(
            rank_correlations=[Decimal("0.90"), Decimal("0.85")],
            top_decile_persistence=Decimal("0.80"),
            turnover_rate=Decimal("0.20"),
        )
    )
    unstable = score_rank_stability(
        RankStabilityInput(
            rank_correlations=[Decimal("0.10"), Decimal("-0.20")],
            top_decile_persistence=Decimal("0.20"),
            turnover_rate=Decimal("0.85"),
        )
    )
    assert stable > unstable


def test_breadth_stability_penalizes_narrow_universe_dependency() -> None:
    config = EntryRobustnessConfig()
    broad = score_breadth_stability(
        BreadthStabilityInput(
            performances={
                "top_500": Decimal("0.06"),
                "top_1000": Decimal("0.055"),
                "top_2000": Decimal("0.05"),
            }
        ),
        config=config,
    )
    narrow = score_breadth_stability(
        BreadthStabilityInput(
            performances={
                "top_500": Decimal("0.08"),
                "full_universe": Decimal("-0.01"),
            }
        ),
        config=config,
    )
    assert broad > narrow


def test_sample_stability_penalizes_period_divergence() -> None:
    config = EntryRobustnessConfig()
    stable = score_sample_stability(
        SampleStabilityInput(
            periods=[
                SamplePeriodMetrics(
                    period_name=SamplePeriod.IN_SAMPLE.value,
                    mean_ic=Decimal("0.06"),
                    mean_forward_return=Decimal("0.03"),
                    hit_rate=Decimal("0.62"),
                ),
                SamplePeriodMetrics(
                    period_name=SamplePeriod.OUT_OF_SAMPLE.value,
                    mean_ic=Decimal("0.065"),
                    mean_forward_return=Decimal("0.032"),
                    hit_rate=Decimal("0.63"),
                ),
            ]
        ),
        config=config,
    )
    unstable = score_sample_stability(
        SampleStabilityInput(
            periods=[
                SamplePeriodMetrics(
                    period_name=SamplePeriod.IN_SAMPLE.value,
                    mean_ic=Decimal("0.08"),
                    mean_forward_return=Decimal("0.05"),
                    hit_rate=Decimal("0.75"),
                ),
                SamplePeriodMetrics(
                    period_name=SamplePeriod.OUT_OF_SAMPLE.value,
                    mean_ic=Decimal("-0.04"),
                    mean_forward_return=Decimal("-0.05"),
                    hit_rate=Decimal("0.30"),
                ),
            ]
        ),
        config=config,
    )
    assert stable > unstable
