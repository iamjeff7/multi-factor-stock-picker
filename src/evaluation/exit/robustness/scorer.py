"""Exit robustness scorer."""

from __future__ import annotations

from evaluation.exit.robustness.components import (
    score_holding_period_stability,
    score_parameter_stability,
    score_performance_stability,
    score_regime_stability,
    score_risk_stability,
    score_sample_stability,
    score_trade_distribution_stability,
)
from evaluation.exit.robustness.config import ExitRobustnessConfig
from evaluation.exit.robustness.validator import ExitRobustnessValidator
from evaluation.robustness.classification import classify_robustness_score
from evaluation.robustness.normalize import quantize_score
from schemas.exit_robustness import ExitRobustnessInputs, ExitRobustnessResult


class ExitRobustnessScorer:
    """Computes weighted exit signal robustness scores across seven dimensions."""

    def __init__(
        self,
        *,
        config: ExitRobustnessConfig | None = None,
        validator: ExitRobustnessValidator | None = None,
    ) -> None:
        self._config = config or ExitRobustnessConfig()
        self._validator = validator or ExitRobustnessValidator()

    @property
    def config(self) -> ExitRobustnessConfig:
        return self._config

    def score(
        self,
        inputs: ExitRobustnessInputs,
        *,
        config: ExitRobustnessConfig | None = None,
    ) -> ExitRobustnessResult:
        scoring_config = config or self._config
        self._validator.validate_config_or_raise(scoring_config)
        self._validator.validate_inputs_or_raise(inputs)

        performance_stability_score = quantize_score(
            score_performance_stability(inputs.performance_stability, config=scoring_config)
        )
        regime_stability_score = quantize_score(
            score_regime_stability(inputs.regime_stability, config=scoring_config)
        )
        parameter_stability_score = quantize_score(
            score_parameter_stability(inputs.parameter_stability, config=scoring_config)
        )
        holding_period_stability_score = quantize_score(
            score_holding_period_stability(
                inputs.holding_period_stability,
                config=scoring_config,
            )
        )
        sample_stability_score = quantize_score(
            score_sample_stability(inputs.sample_stability, config=scoring_config)
        )
        trade_distribution_stability_score = quantize_score(
            score_trade_distribution_stability(
                inputs.trade_distribution_stability,
                config=scoring_config,
            )
        )
        risk_stability_score = quantize_score(
            score_risk_stability(inputs.risk_stability, config=scoring_config)
        )

        weights = scoring_config.component_weights
        overall_robustness_score = quantize_score(
            performance_stability_score * weights.performance_stability
            + regime_stability_score * weights.regime_stability
            + parameter_stability_score * weights.parameter_stability
            + holding_period_stability_score * weights.holding_period_stability
            + sample_stability_score * weights.sample_stability
            + trade_distribution_stability_score * weights.trade_distribution_stability
            + risk_stability_score * weights.risk_stability
        )
        classification = classify_robustness_score(
            overall_robustness_score,
            thresholds=scoring_config.classification_thresholds,
        )

        result = ExitRobustnessResult(
            exit_signal_id=inputs.exit_signal_id,
            performance_stability_score=performance_stability_score,
            regime_stability_score=regime_stability_score,
            parameter_stability_score=parameter_stability_score,
            holding_period_stability_score=holding_period_stability_score,
            sample_stability_score=sample_stability_score,
            trade_distribution_stability_score=trade_distribution_stability_score,
            risk_stability_score=risk_stability_score,
            overall_robustness_score=overall_robustness_score,
            robustness_classification=classification.value,
        )
        self._validator.validate_result_or_raise(result, config=scoring_config)
        return result
