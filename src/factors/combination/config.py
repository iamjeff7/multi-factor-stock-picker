"""Factor combination configuration."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from core.types import SignalId
from factors.combination.enums import (
    CombinationMethod,
    MissingFactorPolicy,
    WeightingMethod,
)


class ScoreRange(BaseModel):
    min: Decimal = Decimal("0.0")
    max: Decimal = Decimal("1.0")

    @model_validator(mode="after")
    def validate_bounds(self) -> ScoreRange:
        if self.min >= self.max:
            raise ValueError("score_range.min must be less than score_range.max")
        return self


class FactorCombinationConfig(BaseModel):
    combination_method: CombinationMethod = CombinationMethod.WEIGHTED_MEAN
    weighting_method: WeightingMethod = WeightingMethod.EQUAL_WEIGHT
    factor_weights: dict[str, Decimal] = Field(default_factory=dict)
    missing_factor_policy: MissingFactorPolicy = MissingFactorPolicy.IGNORE_MISSING_FACTOR
    minimum_factor_coverage_pct: Decimal = Field(default=Decimal("0.50"), ge=Decimal("0"), le=Decimal("1"))
    score_range: ScoreRange = Field(default_factory=ScoreRange)

    @model_validator(mode="after")
    def validate_factor_weights(self) -> FactorCombinationConfig:
        if not self.factor_weights:
            raise ValueError("factor_weights must define at least one enabled factor")
        for signal_id, weight in self.factor_weights.items():
            if weight < Decimal("0"):
                raise ValueError(f"Weight for {signal_id} must be non-negative")
        return self

    @property
    def enabled_factors(self) -> tuple[SignalId, ...]:
        return tuple(SignalId(signal_id) for signal_id in sorted(self.factor_weights))

    def normalized_weights(self) -> dict[SignalId, Decimal]:
        if self.weighting_method == WeightingMethod.EQUAL_WEIGHT:
            raw_weights = {signal_id: Decimal("1") for signal_id in self.enabled_factors}
        else:
            raw_weights = {
                SignalId(signal_id): weight
                for signal_id, weight in self.factor_weights.items()
            }

        total = sum(raw_weights.values(), start=Decimal("0"))
        if total == Decimal("0"):
            raise ValueError("Sum of factor weights must be greater than zero")
        return {signal_id: weight / total for signal_id, weight in raw_weights.items()}
