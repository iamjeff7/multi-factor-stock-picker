"""Combined strategy robustness scoring."""

from __future__ import annotations

from decimal import Decimal

from evaluation.robustness.classification import classify_robustness_score
from evaluation.robustness.normalize import quantize_score
from pydantic import BaseModel, Field, model_validator


class CombinedComponentWeights(BaseModel):
    walk_forward_stability: Decimal = Decimal("0.20")
    out_of_sample_retention: Decimal = Decimal("0.20")
    market_regime_consistency: Decimal = Decimal("0.15")
    parameter_sensitivity: Decimal = Decimal("0.10")
    universe_stability: Decimal = Decimal("0.10")
    transaction_cost_resilience: Decimal = Decimal("0.10")
    factor_decay_resistance: Decimal = Decimal("0.10")
    data_perturbation_resilience: Decimal = Decimal("0.05")

    @model_validator(mode="after")
    def validate_total_weight(self) -> CombinedComponentWeights:
        total = (
            self.walk_forward_stability
            + self.out_of_sample_retention
            + self.market_regime_consistency
            + self.parameter_sensitivity
            + self.universe_stability
            + self.transaction_cost_resilience
            + self.factor_decay_resistance
            + self.data_perturbation_resilience
        )
        if total != Decimal("1"):
            raise ValueError(f"Component weights must sum to 1.0, got {total}")
        return self


class CombinedRobustnessConfig(BaseModel):
    component_weights: CombinedComponentWeights = Field(default_factory=CombinedComponentWeights)


PENDING_COMBINED_ROBUSTNESS_DIMENSIONS = (
    "walk_forward_stability",
    "out_of_sample_retention",
    "market_regime_consistency",
    "parameter_sensitivity",
    "universe_stability",
    "transaction_cost_resilience",
    "factor_decay_resistance",
    "data_perturbation_resilience",
)


class CombinedRobustnessResult(BaseModel):
    walk_forward_stability_score: Decimal = Decimal("0")
    out_of_sample_retention_score: Decimal = Decimal("0")
    market_regime_consistency_score: Decimal = Decimal("0")
    parameter_sensitivity_score: Decimal = Decimal("0")
    universe_stability_score: Decimal = Decimal("0")
    transaction_cost_resilience_score: Decimal = Decimal("0")
    factor_decay_resistance_score: Decimal = Decimal("0")
    data_perturbation_resilience_score: Decimal = Decimal("0")
    overall_robustness_score: Decimal = Decimal("0")
    robustness_classification: str = "REJECT"
    pending_dimensions: list[str] = Field(default_factory=lambda: list(PENDING_COMBINED_ROBUSTNESS_DIMENSIONS))


def compute_combined_robustness(
    *,
    config: CombinedRobustnessConfig | None = None,
) -> CombinedRobustnessResult:
    """Return pending combined robustness until full strategy inputs are wired."""
    _ = config
    return CombinedRobustnessResult(
        pending_dimensions=list(PENDING_COMBINED_ROBUSTNESS_DIMENSIONS),
        overall_robustness_score=Decimal("0"),
        robustness_classification=classify_robustness_score(Decimal("0")).value,
    )


def score_from_active_components(
    *,
    component_scores: dict[str, Decimal],
    pending_dimensions: list[str],
    config: CombinedRobustnessConfig,
) -> Decimal:
    weights = config.component_weights
    active_weight = sum(
        getattr(weights, key)
        for key in component_scores
        if key not in pending_dimensions
    )
    if active_weight <= Decimal("0"):
        return Decimal("0")
    score = sum(
        component_scores[key] * getattr(weights, key)
        for key in component_scores
        if key not in pending_dimensions
    ) / active_weight
    return quantize_score(score)
