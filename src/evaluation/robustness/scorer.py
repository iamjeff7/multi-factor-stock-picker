"""Entry robustness scorer."""

from __future__ import annotations

from decimal import Decimal

from evaluation.robustness.classification import classify_robustness_score
from evaluation.robustness.components import (
    score_factor_decay_resistance,
    score_ic_stability,
    score_out_of_sample_retention,
    score_parameter_stability,
    score_regime_stability,
    score_return_stability,
)
from evaluation.robustness.config import EntryRobustnessConfig
from evaluation.robustness.normalize import quantize_score
from evaluation.robustness.validator import EntryRobustnessValidator
from schemas.robustness import EntryRobustnessInputs, EntryRobustnessResult


class EntryRobustnessScorer:
    """Computes weighted entry signal robustness scores across eight dimensions."""

    def __init__(
        self,
        *,
        config: EntryRobustnessConfig | None = None,
        validator: EntryRobustnessValidator | None = None,
    ) -> None:
        self._config = config or EntryRobustnessConfig()
        self._validator = validator or EntryRobustnessValidator()

    @property
    def config(self) -> EntryRobustnessConfig:
        return self._config

    def score(
        self,
        inputs: EntryRobustnessInputs,
        *,
        config: EntryRobustnessConfig | None = None,
    ) -> EntryRobustnessResult:
        scoring_config = config or self._config
        self._validator.validate_config_or_raise(scoring_config)
        self._validator.validate_inputs_or_raise(inputs)

        ic_stability_score = quantize_score(
            score_ic_stability(inputs.ic_stability, config=scoring_config)
        )
        return_stability_score = quantize_score(
            score_return_stability(inputs.return_stability, config=scoring_config)
        )
        walk_forward_stability_score = quantize_score(
            average_return_stability_walk_forward(inputs, config=scoring_config)
        )
        out_of_sample_retention_score = quantize_score(
            score_out_of_sample_retention(inputs.sample_stability, config=scoring_config)
        )
        market_regime_consistency_score = quantize_score(
            score_regime_stability(inputs.regime_stability, config=scoring_config)
        )
        parameter_sensitivity_score = quantize_score(
            score_parameter_stability(inputs.parameter_stability, config=scoring_config)
        )
        ic_values = [period.mean_ic for period in inputs.sample_stability.periods]
        factor_decay_resistance_score = quantize_score(
            score_factor_decay_resistance(ic_values) if ic_values else Decimal("0")
        )
        data_perturbation_resilience_score = Decimal("0")

        weights = scoring_config.component_weights
        overall_robustness_score = quantize_score(
            ic_stability_score * weights.ic_stability
            + return_stability_score * weights.return_stability
            + walk_forward_stability_score * weights.walk_forward_stability
            + out_of_sample_retention_score * weights.out_of_sample_retention
            + market_regime_consistency_score * weights.market_regime_consistency
            + parameter_sensitivity_score * weights.parameter_sensitivity
            + factor_decay_resistance_score * weights.factor_decay_resistance
            + data_perturbation_resilience_score * weights.data_perturbation_resilience
        )
        classification = classify_robustness_score(
            overall_robustness_score,
            thresholds=scoring_config.classification_thresholds,
        )

        result = EntryRobustnessResult(
            signal_id=inputs.signal_id,
            ic_stability_score=ic_stability_score,
            return_stability_score=return_stability_score,
            walk_forward_stability_score=walk_forward_stability_score,
            out_of_sample_retention_score=out_of_sample_retention_score,
            market_regime_consistency_score=market_regime_consistency_score,
            parameter_sensitivity_score=parameter_sensitivity_score,
            factor_decay_resistance_score=factor_decay_resistance_score,
            data_perturbation_resilience_score=data_perturbation_resilience_score,
            overall_robustness_score=overall_robustness_score,
            robustness_classification=classification.value,
        )
        self._validator.validate_result_or_raise(result, config=scoring_config)
        return result


def average_return_stability_walk_forward(
    inputs: EntryRobustnessInputs,
    *,
    config: EntryRobustnessConfig,
) -> Decimal:
    ic_values = [period.mean_ic for period in inputs.sample_stability.periods]
    if len(ic_values) >= 4:
        from evaluation.robustness.components import score_walk_forward_stability_from_ic_series

        return score_walk_forward_stability_from_ic_series(ic_values, config=config)
    return score_return_stability(inputs.return_stability, config=config)
