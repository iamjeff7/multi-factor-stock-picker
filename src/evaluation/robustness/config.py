"""Entry robustness configuration."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class ComponentWeights(BaseModel):
    ic_stability: Decimal = Decimal("0.25")
    return_stability: Decimal = Decimal("0.20")
    regime_stability: Decimal = Decimal("0.15")
    parameter_stability: Decimal = Decimal("0.15")
    rank_stability: Decimal = Decimal("0.10")
    breadth_stability: Decimal = Decimal("0.10")
    sample_stability: Decimal = Decimal("0.05")

    @model_validator(mode="after")
    def validate_total_weight(self) -> ComponentWeights:
        total = (
            self.ic_stability
            + self.return_stability
            + self.regime_stability
            + self.parameter_stability
            + self.rank_stability
            + self.breadth_stability
            + self.sample_stability
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
