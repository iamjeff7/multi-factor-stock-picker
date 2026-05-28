"""Entry robustness configuration."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class ComponentWeights(BaseModel):
    ic_stability: Decimal = Decimal("0.15")
    return_stability: Decimal = Decimal("0.10")
    walk_forward_stability: Decimal = Decimal("0.20")
    out_of_sample_retention: Decimal = Decimal("0.20")
    market_regime_consistency: Decimal = Decimal("0.15")
    parameter_sensitivity: Decimal = Decimal("0.10")
    factor_decay_resistance: Decimal = Decimal("0.05")
    data_perturbation_resilience: Decimal = Decimal("0.05")

    @model_validator(mode="after")
    def validate_total_weight(self) -> ComponentWeights:
        total = (
            self.ic_stability
            + self.return_stability
            + self.walk_forward_stability
            + self.out_of_sample_retention
            + self.market_regime_consistency
            + self.parameter_sensitivity
            + self.factor_decay_resistance
            + self.data_perturbation_resilience
        )
        if total != Decimal("1"):
            raise ValueError(f"Component weights must sum to 1.0, got {total}")
        return self


class ClassificationThresholds(BaseModel):
    exceptional: Decimal = Decimal("0.90")
    strong: Decimal = Decimal("0.80")
    good: Decimal = Decimal("0.70")
    acceptable: Decimal = Decimal("0.60")
    weak: Decimal = Decimal("0.50")

    @model_validator(mode="after")
    def validate_ordering(self) -> ClassificationThresholds:
        values = [
            self.exceptional,
            self.strong,
            self.good,
            self.acceptable,
            self.weak,
        ]
        if values != sorted(values, reverse=True):
            raise ValueError("Classification thresholds must be descending")
        return self


class EntryRobustnessConfig(BaseModel):
    component_weights: ComponentWeights = Field(default_factory=ComponentWeights)
    classification_thresholds: ClassificationThresholds = Field(
        default_factory=ClassificationThresholds,
    )
    ic_level_floor: Decimal = Decimal("-0.05")
    ic_level_ceiling: Decimal = Decimal("0.10")
    ic_std_ceiling: Decimal = Decimal("0.15")
    ic_ir_ceiling: Decimal = Decimal("1.5")
    return_level_floor: Decimal = Decimal("-0.05")
    return_level_ceiling: Decimal = Decimal("0.10")
    return_std_ceiling: Decimal = Decimal("0.10")
