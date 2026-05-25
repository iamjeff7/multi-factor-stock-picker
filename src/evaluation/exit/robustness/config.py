"""Exit robustness configuration."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from evaluation.robustness.config import ClassificationThresholds


class ExitComponentWeights(BaseModel):
    performance_stability: Decimal = Decimal("0.25")
    regime_stability: Decimal = Decimal("0.15")
    parameter_stability: Decimal = Decimal("0.20")
    holding_period_stability: Decimal = Decimal("0.10")
    sample_stability: Decimal = Decimal("0.10")
    trade_distribution_stability: Decimal = Decimal("0.10")
    risk_stability: Decimal = Decimal("0.10")

    @model_validator(mode="after")
    def validate_total_weight(self) -> ExitComponentWeights:
        total = (
            self.performance_stability
            + self.regime_stability
            + self.parameter_stability
            + self.holding_period_stability
            + self.sample_stability
            + self.trade_distribution_stability
            + self.risk_stability
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
