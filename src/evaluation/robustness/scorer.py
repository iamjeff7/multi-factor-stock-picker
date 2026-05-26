"""Entry robustness scorer."""

from __future__ import annotations

from evaluation.robustness.classification import classify_robustness_score
from evaluation.robustness.components import (
    score_breadth_stability,
    score_ic_stability,
    score_parameter_stability,
    score_rank_stability,
    score_regime_stability,
    score_return_stability,
    score_sample_stability,
)
from evaluation.robustness.config import EntryRobustnessConfig
from evaluation.robustness.normalize import quantize_score
from evaluation.robustness.validator import EntryRobustnessValidator
from schemas.robustness import EntryRobustnessInputs, EntryRobustnessResult


class EntryRobustnessScorer:
    """Computes weighted entry signal robustness scores across seven dimensions."""

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
        regime_stability_score = quantize_score(
            score_regime_stability(inputs.regime_stability, config=scoring_config)
        )
        parameter_stability_score = quantize_score(
            score_parameter_stability(inputs.parameter_stability, config=scoring_config)
        )
        rank_stability_score = quantize_score(score_rank_stability(inputs.rank_stability))
        breadth_stability_score = quantize_score(
            score_breadth_stability(inputs.breadth_stability, config=scoring_config)
        )
        sample_stability_score = quantize_score(
            score_sample_stability(inputs.sample_stability, config=scoring_config)
        )

        weights = scoring_config.component_weights
        overall_robustness_score = quantize_score(
            ic_stability_score * weights.ic_stability
            + return_stability_score * weights.return_stability
            + regime_stability_score * weights.regime_stability
            + parameter_stability_score * weights.parameter_stability
            + rank_stability_score * weights.rank_stability
            + breadth_stability_score * weights.breadth_stability
            + sample_stability_score * weights.sample_stability
        )
        classification = classify_robustness_score(
            overall_robustness_score,
            thresholds=scoring_config.classification_thresholds,
        )

        result = EntryRobustnessResult(
            signal_id=inputs.signal_id,
            ic_stability_score=ic_stability_score,
            return_stability_score=return_stability_score,
            regime_stability_score=regime_stability_score,
            parameter_stability_score=parameter_stability_score,
            rank_stability_score=rank_stability_score,
            breadth_stability_score=breadth_stability_score,
            sample_stability_score=sample_stability_score,
            overall_robustness_score=overall_robustness_score,
            robustness_classification=classification.value,
        )
        self._validator.validate_result_or_raise(result, config=scoring_config)
        return result
