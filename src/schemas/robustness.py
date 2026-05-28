"""Entry robustness evaluation schemas."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from core.types import SignalId
from schemas.ic import ICSummary


class ICStabilityInput(BaseModel):
    mean_ic: Decimal
    median_ic: Decimal
    std_ic: Decimal | None = None
    hit_rate: Decimal
    ic_information_ratio: Decimal | None = None

    @classmethod
    def from_ic_summary(cls, summary: ICSummary) -> ICStabilityInput:
        return cls(
            mean_ic=summary.mean_ic,
            median_ic=summary.median_ic,
            std_ic=summary.std_ic,
            hit_rate=summary.hit_rate,
            ic_information_ratio=summary.ic_information_ratio,
        )


class ReturnStabilityInput(BaseModel):
    mean_forward_return: Decimal
    median_forward_return: Decimal
    return_std: Decimal | None = None
    positive_period_ratio: Decimal


class RegimeMetrics(BaseModel):
    regime_name: str
    mean_ic: Decimal
    mean_forward_return: Decimal
    hit_rate: Decimal


class RegimeStabilityInput(BaseModel):
    regimes: list[RegimeMetrics] = Field(default_factory=list)


class ParameterStabilityInput(BaseModel):
    performances: list[Decimal] = Field(default_factory=list)


class RankStabilityInput(BaseModel):
    rank_correlations: list[Decimal] = Field(default_factory=list)
    top_decile_persistence: Decimal
    turnover_rate: Decimal


class BreadthStabilityInput(BaseModel):
    performances: dict[str, Decimal] = Field(default_factory=dict)


class SamplePeriodMetrics(BaseModel):
    period_name: str
    mean_ic: Decimal
    mean_forward_return: Decimal
    hit_rate: Decimal


class SampleStabilityInput(BaseModel):
    periods: list[SamplePeriodMetrics] = Field(default_factory=list)


class EntryRobustnessInputs(BaseModel):
    signal_id: SignalId
    ic_stability: ICStabilityInput
    return_stability: ReturnStabilityInput
    regime_stability: RegimeStabilityInput
    parameter_stability: ParameterStabilityInput
    rank_stability: RankStabilityInput
    breadth_stability: BreadthStabilityInput
    sample_stability: SampleStabilityInput


class EntryRobustnessResult(BaseModel):
    signal_id: SignalId
    ic_stability_score: Decimal
    return_stability_score: Decimal
    walk_forward_stability_score: Decimal
    out_of_sample_retention_score: Decimal
    market_regime_consistency_score: Decimal
    parameter_sensitivity_score: Decimal
    factor_decay_resistance_score: Decimal
    data_perturbation_resilience_score: Decimal
    overall_robustness_score: Decimal
    robustness_classification: str
