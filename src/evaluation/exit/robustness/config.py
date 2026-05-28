"""Exit robustness configuration."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from evaluation.robustness.config import ClassificationThresholds


class ExitComponentWeights(BaseModel):
    trade_distribution_stability: Decimal = Decimal("0.10")
    holding_period_stability: Decimal = Decimal("0.10")
    walk_forward_stability: Decimal = Decimal("0.20")
    out_of_sample_retention: Decimal = Decimal("0.20")
    market_regime_consistency: Decimal = Decimal("0.15")
    parameter_sensitivity: Decimal = Decimal("0.10")
    profit_capture_consistency: Decimal = Decimal("0.10")
    data_perturbation_resilience: Decimal = Decimal("0.05")

    @model_validator(mode="after")
    def validate_total_weight(self) -> ExitComponentWeights:
        total = (
            self.trade_distribution_stability
            + self.holding_period_stability
            + self.walk_forward_stability
            + self.out_of_sample_retention
            + self.market_regime_consistency
            + self.parameter_sensitivity
            + self.profit_capture_consistency
            + self.data_perturbation_resilience
        )
        if total != Decimal("1"):
            raise ValueError(f"Component weights must sum to 1.0, got {total}")
        return self


class ExitRobustnessConfig(BaseModel):
    component_weights: ExitComponentWeights = Field(default_factory=ExitComponentWeights)
    classification_thresholds: ClassificationThresholds = Field(
        default_factory=ClassificationThresholds,
    )
    return_level_floor: Decimal = Decimal("-0.05")
    return_level_ceiling: Decimal = Decimal("0.10")
    return_std_ceiling: Decimal = Decimal("0.10")
    profit_factor_floor: Decimal = Decimal("0.50")
    profit_factor_ceiling: Decimal = Decimal("2.00")
    expectancy_floor: Decimal = Decimal("-0.02")
    expectancy_ceiling: Decimal = Decimal("0.05")
    max_drawdown_ceiling: Decimal = Decimal("0.30")
    volatility_ceiling: Decimal = Decimal("0.10")
    tail_risk_ceiling: Decimal = Decimal("0.08")
    concentration_ceiling: Decimal = Decimal("0.50")
