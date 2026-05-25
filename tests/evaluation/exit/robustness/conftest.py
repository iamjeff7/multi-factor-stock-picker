"""Shared helpers for exit robustness tests."""

from __future__ import annotations

from decimal import Decimal

from core.types import SignalId
from core.enums import SamplePeriod
from schemas.exit_robustness import (
    ExitParameterStabilityInput,
    ExitRegimeMetrics,
    ExitRegimeStabilityInput,
    ExitRobustnessInputs,
    ExitSamplePeriodMetrics,
    ExitSampleStabilityInput,
    HoldingPeriodMetrics,
    HoldingPeriodStabilityInput,
    PerformanceStabilityInput,
    RiskStabilityInput,
    TradeDistributionStabilityInput,
)


def strong_exit_robustness_inputs(*, exit_signal_id: str = "trailing_stop_10pct") -> ExitRobustnessInputs:
    return ExitRobustnessInputs(
        exit_signal_id=SignalId(exit_signal_id),
        performance_stability=PerformanceStabilityInput(
            average_trade_return=Decimal("0.04"),
            median_trade_return=Decimal("0.035"),
            win_rate=Decimal("0.62"),
            profit_factor=Decimal("1.8"),
            expectancy=Decimal("0.015"),
            return_volatility=Decimal("0.02"),
        ),
        regime_stability=ExitRegimeStabilityInput(
            regimes=[
                ExitRegimeMetrics(
                    regime_name="bull",
                    average_trade_return=Decimal("0.05"),
                    win_rate=Decimal("0.65"),
                    profit_factor=Decimal("1.9"),
                    expectancy=Decimal("0.018"),
                ),
                ExitRegimeMetrics(
                    regime_name="bear",
                    average_trade_return=Decimal("0.02"),
                    win_rate=Decimal("0.55"),
                    profit_factor=Decimal("1.4"),
                    expectancy=Decimal("0.010"),
                ),
                ExitRegimeMetrics(
                    regime_name="sideways",
                    average_trade_return=Decimal("0.03"),
                    win_rate=Decimal("0.58"),
                    profit_factor=Decimal("1.6"),
                    expectancy=Decimal("0.012"),
                ),
            ]
        ),
        parameter_stability=ExitParameterStabilityInput(
            performances=[Decimal("0.04"), Decimal("0.038"), Decimal("0.035")]
        ),
        holding_period_stability=HoldingPeriodStabilityInput(
            buckets=[
                HoldingPeriodMetrics(
                    bucket_name="1_5",
                    average_return=Decimal("0.03"),
                    win_rate=Decimal("0.58"),
                    profit_factor=Decimal("1.5"),
                ),
                HoldingPeriodMetrics(
                    bucket_name="6_20",
                    average_return=Decimal("0.04"),
                    win_rate=Decimal("0.62"),
                    profit_factor=Decimal("1.7"),
                ),
                HoldingPeriodMetrics(
                    bucket_name="21_60",
                    average_return=Decimal("0.035"),
                    win_rate=Decimal("0.60"),
                    profit_factor=Decimal("1.6"),
                ),
            ]
        ),
        sample_stability=ExitSampleStabilityInput(
            periods=[
                ExitSamplePeriodMetrics(
                    period_name=SamplePeriod.IN_SAMPLE.value,
                    average_return=Decimal("0.035"),
                    win_rate=Decimal("0.60"),
                    profit_factor=Decimal("1.6"),
                ),
                ExitSamplePeriodMetrics(
                    period_name=SamplePeriod.OUT_OF_SAMPLE.value,
                    average_return=Decimal("0.038"),
                    win_rate=Decimal("0.61"),
                    profit_factor=Decimal("1.65"),
                ),
            ]
        ),
        trade_distribution_stability=TradeDistributionStabilityInput(
            profitable_trade_pct=Decimal("0.62"),
            contribution_concentration=Decimal("0.15"),
            top_trade_contribution_ratio=Decimal("0.08"),
            largest_winner_contribution=Decimal("0.05"),
        ),
        risk_stability=RiskStabilityInput(
            max_drawdown=Decimal("0.08"),
            trade_loss_std=Decimal("0.02"),
            volatility=Decimal("0.03"),
            tail_risk=Decimal("0.04"),
        ),
    )


def weak_exit_robustness_inputs(*, exit_signal_id: str = "weak_exit") -> ExitRobustnessInputs:
    return ExitRobustnessInputs(
        exit_signal_id=SignalId(exit_signal_id),
        performance_stability=PerformanceStabilityInput(
            average_trade_return=Decimal("-0.02"),
            median_trade_return=Decimal("-0.015"),
            win_rate=Decimal("0.38"),
            profit_factor=Decimal("0.8"),
            expectancy=Decimal("-0.01"),
            return_volatility=Decimal("0.08"),
        ),
        regime_stability=ExitRegimeStabilityInput(
            regimes=[
                ExitRegimeMetrics(
                    regime_name="bull",
                    average_trade_return=Decimal("0.03"),
                    win_rate=Decimal("0.52"),
                    profit_factor=Decimal("1.2"),
                    expectancy=Decimal("0.005"),
                ),
                ExitRegimeMetrics(
                    regime_name="bear",
                    average_trade_return=Decimal("-0.05"),
                    win_rate=Decimal("0.30"),
                    profit_factor=Decimal("0.6"),
                    expectancy=Decimal("-0.02"),
                ),
            ]
        ),
        parameter_stability=ExitParameterStabilityInput(
            performances=[Decimal("0.03"), Decimal("-0.01"), Decimal("-0.04")]
        ),
        holding_period_stability=HoldingPeriodStabilityInput(
            buckets=[
                HoldingPeriodMetrics(
                    bucket_name="1_5",
                    average_return=Decimal("0.06"),
                    win_rate=Decimal("0.70"),
                    profit_factor=Decimal("2.0"),
                ),
                HoldingPeriodMetrics(
                    bucket_name="21_60",
                    average_return=Decimal("-0.04"),
                    win_rate=Decimal("0.35"),
                    profit_factor=Decimal("0.7"),
                ),
            ]
        ),
        sample_stability=ExitSampleStabilityInput(
            periods=[
                ExitSamplePeriodMetrics(
                    period_name=SamplePeriod.IN_SAMPLE.value,
                    average_return=Decimal("0.04"),
                    win_rate=Decimal("0.58"),
                    profit_factor=Decimal("1.5"),
                ),
                ExitSamplePeriodMetrics(
                    period_name=SamplePeriod.OUT_OF_SAMPLE.value,
                    average_return=Decimal("-0.05"),
                    win_rate=Decimal("0.32"),
                    profit_factor=Decimal("0.7"),
                ),
            ]
        ),
        trade_distribution_stability=TradeDistributionStabilityInput(
            profitable_trade_pct=Decimal("0.38"),
            contribution_concentration=Decimal("0.45"),
            top_trade_contribution_ratio=Decimal("0.35"),
            largest_winner_contribution=Decimal("0.25"),
        ),
        risk_stability=RiskStabilityInput(
            max_drawdown=Decimal("0.25"),
            trade_loss_std=Decimal("0.06"),
            volatility=Decimal("0.09"),
            tail_risk=Decimal("0.07"),
        ),
    )
