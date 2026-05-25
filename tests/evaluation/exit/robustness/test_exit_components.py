"""Exit robustness component scorer tests."""

from decimal import Decimal

from core.enums import SamplePeriod
from evaluation.exit.robustness.components import (
    score_holding_period_stability,
    score_performance_stability,
    score_risk_stability,
    score_sample_stability,
    score_trade_distribution_stability,
)
from evaluation.exit.robustness.config import ExitRobustnessConfig
from schemas.exit_robustness import (
    ExitSamplePeriodMetrics,
    ExitSampleStabilityInput,
    HoldingPeriodMetrics,
    HoldingPeriodStabilityInput,
    PerformanceStabilityInput,
    RiskStabilityInput,
    TradeDistributionStabilityInput,
)


def test_performance_stability_penalizes_high_volatility() -> None:
    config = ExitRobustnessConfig()
    stable = score_performance_stability(
        PerformanceStabilityInput(
            average_trade_return=Decimal("0.04"),
            median_trade_return=Decimal("0.04"),
            win_rate=Decimal("0.65"),
            profit_factor=Decimal("1.8"),
            expectancy=Decimal("0.015"),
            return_volatility=Decimal("0.01"),
        ),
        config=config,
    )
    unstable = score_performance_stability(
        PerformanceStabilityInput(
            average_trade_return=Decimal("0.04"),
            median_trade_return=Decimal("0.04"),
            win_rate=Decimal("0.65"),
            profit_factor=Decimal("1.8"),
            expectancy=Decimal("0.015"),
            return_volatility=Decimal("0.09"),
        ),
        config=config,
    )
    assert stable > unstable


def test_holding_period_stability_penalizes_narrow_effectiveness() -> None:
    config = ExitRobustnessConfig()
    broad = score_holding_period_stability(
        HoldingPeriodStabilityInput(
            buckets=[
                HoldingPeriodMetrics(
                    bucket_name="1_5",
                    average_return=Decimal("0.04"),
                    win_rate=Decimal("0.60"),
                    profit_factor=Decimal("1.6"),
                ),
                HoldingPeriodMetrics(
                    bucket_name="6_20",
                    average_return=Decimal("0.038"),
                    win_rate=Decimal("0.58"),
                    profit_factor=Decimal("1.55"),
                ),
            ]
        ),
        config=config,
    )
    narrow = score_holding_period_stability(
        HoldingPeriodStabilityInput(
            buckets=[
                HoldingPeriodMetrics(
                    bucket_name="1_5",
                    average_return=Decimal("0.08"),
                    win_rate=Decimal("0.75"),
                    profit_factor=Decimal("2.2"),
                ),
                HoldingPeriodMetrics(
                    bucket_name="21_60",
                    average_return=Decimal("-0.03"),
                    win_rate=Decimal("0.35"),
                    profit_factor=Decimal("0.7"),
                ),
            ]
        ),
        config=config,
    )
    assert broad > narrow


def test_trade_distribution_stability_penalizes_concentration() -> None:
    config = ExitRobustnessConfig()
    distributed = score_trade_distribution_stability(
        TradeDistributionStabilityInput(
            profitable_trade_pct=Decimal("0.65"),
            contribution_concentration=Decimal("0.10"),
            top_trade_contribution_ratio=Decimal("0.08"),
            largest_winner_contribution=Decimal("0.05"),
        ),
        config=config,
    )
    concentrated = score_trade_distribution_stability(
        TradeDistributionStabilityInput(
            profitable_trade_pct=Decimal("0.65"),
            contribution_concentration=Decimal("0.45"),
            top_trade_contribution_ratio=Decimal("0.40"),
            largest_winner_contribution=Decimal("0.30"),
        ),
        config=config,
    )
    assert distributed > concentrated


def test_risk_stability_rewards_low_drawdown_and_tail_risk() -> None:
    config = ExitRobustnessConfig()
    stable = score_risk_stability(
        RiskStabilityInput(
            max_drawdown=Decimal("0.06"),
            trade_loss_std=Decimal("0.02"),
            volatility=Decimal("0.03"),
            tail_risk=Decimal("0.03"),
        ),
        config=config,
    )
    unstable = score_risk_stability(
        RiskStabilityInput(
            max_drawdown=Decimal("0.28"),
            trade_loss_std=Decimal("0.07"),
            volatility=Decimal("0.09"),
            tail_risk=Decimal("0.075"),
        ),
        config=config,
    )
    assert stable > unstable


def test_sample_stability_penalizes_period_divergence() -> None:
    config = ExitRobustnessConfig()
    stable = score_sample_stability(
        ExitSampleStabilityInput(
            periods=[
                ExitSamplePeriodMetrics(
                    period_name=SamplePeriod.IN_SAMPLE.value,
                    average_return=Decimal("0.04"),
                    win_rate=Decimal("0.60"),
                    profit_factor=Decimal("1.6"),
                ),
                ExitSamplePeriodMetrics(
                    period_name=SamplePeriod.OUT_OF_SAMPLE.value,
                    average_return=Decimal("0.038"),
                    win_rate=Decimal("0.58"),
                    profit_factor=Decimal("1.55"),
                ),
            ]
        ),
        config=config,
    )
    unstable = score_sample_stability(
        ExitSampleStabilityInput(
            periods=[
                ExitSamplePeriodMetrics(
                    period_name=SamplePeriod.IN_SAMPLE.value,
                    average_return=Decimal("0.06"),
                    win_rate=Decimal("0.70"),
                    profit_factor=Decimal("2.0"),
                ),
                ExitSamplePeriodMetrics(
                    period_name=SamplePeriod.OUT_OF_SAMPLE.value,
                    average_return=Decimal("-0.04"),
                    win_rate=Decimal("0.30"),
                    profit_factor=Decimal("0.7"),
                ),
            ]
        ),
        config=config,
    )
    assert stable > unstable
