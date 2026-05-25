"""Shared helpers for entry robustness tests."""

from __future__ import annotations

from decimal import Decimal

from core.types import SignalId
from core.enums import SamplePeriod
from schemas.robustness import (
    BreadthStabilityInput,
    EntryRobustnessInputs,
    ICStabilityInput,
    ParameterStabilityInput,
    RankStabilityInput,
    RegimeMetrics,
    RegimeStabilityInput,
    ReturnStabilityInput,
    SamplePeriodMetrics,
    SampleStabilityInput,
)


def strong_robustness_inputs(*, signal_id: str = "momentum_12m") -> EntryRobustnessInputs:
    return EntryRobustnessInputs(
        signal_id=SignalId(signal_id),
        ic_stability=ICStabilityInput(
            mean_ic=Decimal("0.08"),
            median_ic=Decimal("0.07"),
            std_ic=Decimal("0.03"),
            hit_rate=Decimal("0.70"),
            ic_information_ratio=Decimal("1.2"),
        ),
        return_stability=ReturnStabilityInput(
            mean_forward_return=Decimal("0.04"),
            median_forward_return=Decimal("0.035"),
            return_std=Decimal("0.02"),
            positive_period_ratio=Decimal("0.75"),
        ),
        regime_stability=RegimeStabilityInput(
            regimes=[
                RegimeMetrics(
                    regime_name="bull",
                    mean_ic=Decimal("0.07"),
                    mean_forward_return=Decimal("0.05"),
                    hit_rate=Decimal("0.68"),
                ),
                RegimeMetrics(
                    regime_name="bear",
                    mean_ic=Decimal("0.04"),
                    mean_forward_return=Decimal("0.02"),
                    hit_rate=Decimal("0.58"),
                ),
                RegimeMetrics(
                    regime_name="sideways",
                    mean_ic=Decimal("0.05"),
                    mean_forward_return=Decimal("0.03"),
                    hit_rate=Decimal("0.60"),
                ),
            ]
        ),
        parameter_stability=ParameterStabilityInput(
            performances=[
                Decimal("0.07"),
                Decimal("0.065"),
                Decimal("0.06"),
            ]
        ),
        rank_stability=RankStabilityInput(
            rank_correlations=[Decimal("0.80"), Decimal("0.75"), Decimal("0.78")],
            top_decile_persistence=Decimal("0.70"),
            turnover_rate=Decimal("0.25"),
        ),
        breadth_stability=BreadthStabilityInput(
            performances={
                "top_500": Decimal("0.06"),
                "top_1000": Decimal("0.055"),
                "top_2000": Decimal("0.05"),
            }
        ),
        sample_stability=SampleStabilityInput(
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
    )


def weak_robustness_inputs(*, signal_id: str = "weak_signal") -> EntryRobustnessInputs:
    return EntryRobustnessInputs(
        signal_id=SignalId(signal_id),
        ic_stability=ICStabilityInput(
            mean_ic=Decimal("-0.02"),
            median_ic=Decimal("-0.01"),
            std_ic=Decimal("0.12"),
            hit_rate=Decimal("0.40"),
            ic_information_ratio=Decimal("-0.2"),
        ),
        return_stability=ReturnStabilityInput(
            mean_forward_return=Decimal("-0.03"),
            median_forward_return=Decimal("-0.02"),
            return_std=Decimal("0.08"),
            positive_period_ratio=Decimal("0.35"),
        ),
        regime_stability=RegimeStabilityInput(
            regimes=[
                RegimeMetrics(
                    regime_name="bull",
                    mean_ic=Decimal("0.03"),
                    mean_forward_return=Decimal("0.01"),
                    hit_rate=Decimal("0.52"),
                ),
                RegimeMetrics(
                    regime_name="bear",
                    mean_ic=Decimal("-0.05"),
                    mean_forward_return=Decimal("-0.04"),
                    hit_rate=Decimal("0.30"),
                ),
            ]
        ),
        parameter_stability=ParameterStabilityInput(
            performances=[Decimal("0.05"), Decimal("-0.01"), Decimal("-0.04")]
        ),
        rank_stability=RankStabilityInput(
            rank_correlations=[Decimal("0.10"), Decimal("-0.05")],
            top_decile_persistence=Decimal("0.20"),
            turnover_rate=Decimal("0.80"),
        ),
        breadth_stability=BreadthStabilityInput(
            performances={
                "top_500": Decimal("0.05"),
                "full_universe": Decimal("-0.02"),
            }
        ),
        sample_stability=SampleStabilityInput(
            periods=[
                SamplePeriodMetrics(
                    period_name=SamplePeriod.IN_SAMPLE.value,
                    mean_ic=Decimal("0.04"),
                    mean_forward_return=Decimal("0.02"),
                    hit_rate=Decimal("0.55"),
                ),
                SamplePeriodMetrics(
                    period_name=SamplePeriod.OUT_OF_SAMPLE.value,
                    mean_ic=Decimal("-0.03"),
                    mean_forward_return=Decimal("-0.04"),
                    hit_rate=Decimal("0.35"),
                ),
            ]
        ),
    )
