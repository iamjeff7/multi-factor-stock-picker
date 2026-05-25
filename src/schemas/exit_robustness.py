"""Exit robustness evaluation schemas."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from core.types import SignalId


class PerformanceStabilityInput(BaseModel):
    average_trade_return: Decimal
    median_trade_return: Decimal
    win_rate: Decimal
    profit_factor: Decimal
    expectancy: Decimal
    return_volatility: Decimal | None = None


class ExitRegimeMetrics(BaseModel):
    regime_name: str
    average_trade_return: Decimal
    win_rate: Decimal
    profit_factor: Decimal
    expectancy: Decimal


class ExitRegimeStabilityInput(BaseModel):
    regimes: list[ExitRegimeMetrics] = Field(default_factory=list)


class ExitParameterStabilityInput(BaseModel):
    performances: list[Decimal] = Field(default_factory=list)


class HoldingPeriodMetrics(BaseModel):
    bucket_name: str
    average_return: Decimal
    win_rate: Decimal
    profit_factor: Decimal


class HoldingPeriodStabilityInput(BaseModel):
    buckets: list[HoldingPeriodMetrics] = Field(default_factory=list)


class ExitSamplePeriodMetrics(BaseModel):
    period_name: str
    average_return: Decimal
    win_rate: Decimal
    profit_factor: Decimal


class ExitSampleStabilityInput(BaseModel):
    periods: list[ExitSamplePeriodMetrics] = Field(default_factory=list)


class TradeDistributionStabilityInput(BaseModel):
    profitable_trade_pct: Decimal
    contribution_concentration: Decimal
    top_trade_contribution_ratio: Decimal
    largest_winner_contribution: Decimal


class RiskStabilityInput(BaseModel):
    max_drawdown: Decimal
    trade_loss_std: Decimal | None = None
    volatility: Decimal | None = None
    tail_risk: Decimal | None = None


class ExitRobustnessInputs(BaseModel):
    exit_signal_id: SignalId
    performance_stability: PerformanceStabilityInput
    regime_stability: ExitRegimeStabilityInput
    parameter_stability: ExitParameterStabilityInput
    holding_period_stability: HoldingPeriodStabilityInput
    sample_stability: ExitSampleStabilityInput
    trade_distribution_stability: TradeDistributionStabilityInput
    risk_stability: RiskStabilityInput


class ExitRobustnessResult(BaseModel):
    exit_signal_id: SignalId
    performance_stability_score: Decimal
    regime_stability_score: Decimal
    parameter_stability_score: Decimal
    holding_period_stability_score: Decimal
    sample_stability_score: Decimal
    trade_distribution_stability_score: Decimal
    risk_stability_score: Decimal
    overall_robustness_score: Decimal
    robustness_classification: str
