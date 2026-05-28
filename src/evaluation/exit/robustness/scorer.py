"""Exit robustness scorer."""

from __future__ import annotations

from decimal import Decimal

from evaluation.exit.robustness.components import (
    score_holding_period_stability,
    score_out_of_sample_retention,
    score_parameter_stability,
    score_profit_capture_consistency,
    score_regime_stability,
    score_trade_distribution_stability,
    score_walk_forward_stability,
)
from evaluation.exit.robustness.config import ExitRobustnessConfig
from evaluation.exit.robustness.validator import ExitRobustnessValidator
from evaluation.robustness.classification import classify_robustness_score
from evaluation.robustness.normalize import quantize_score
from schemas.exit_robustness import ExitRobustnessInputs, ExitRobustnessResult


class ExitRobustnessScorer:
    """Computes weighted exit signal robustness scores across eight dimensions."""

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

        trade_distribution_stability_score = quantize_score(
            score_trade_distribution_stability(
                inputs.trade_distribution_stability,
                config=scoring_config,
            )
        )
        holding_period_stability_score = quantize_score(
            score_holding_period_stability(
                inputs.holding_period_stability,
                config=scoring_config,
            )
        )
        walk_forward_stability_score = quantize_score(
            score_walk_forward_stability(inputs.performance_stability, config=scoring_config)
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
        capture_ratios = [
            max(Decimal("0"), period.average_return)
            for period in inputs.sample_stability.periods
        ]
        profit_capture_consistency_score = quantize_score(
            score_profit_capture_consistency(capture_ratios)
        )
        data_perturbation_resilience_score = Decimal("0")

        weights = scoring_config.component_weights
        overall_robustness_score = quantize_score(
            trade_distribution_stability_score * weights.trade_distribution_stability
            + holding_period_stability_score * weights.holding_period_stability
            + walk_forward_stability_score * weights.walk_forward_stability
            + out_of_sample_retention_score * weights.out_of_sample_retention
            + market_regime_consistency_score * weights.market_regime_consistency
            + parameter_sensitivity_score * weights.parameter_sensitivity
            + profit_capture_consistency_score * weights.profit_capture_consistency
            + data_perturbation_resilience_score * weights.data_perturbation_resilience
        )
        classification = classify_robustness_score(
            overall_robustness_score,
            thresholds=scoring_config.classification_thresholds,
        )

        result = ExitRobustnessResult(
            exit_signal_id=inputs.exit_signal_id,
            trade_distribution_stability_score=trade_distribution_stability_score,
            holding_period_stability_score=holding_period_stability_score,
            walk_forward_stability_score=walk_forward_stability_score,
            out_of_sample_retention_score=out_of_sample_retention_score,
            market_regime_consistency_score=market_regime_consistency_score,
            parameter_sensitivity_score=parameter_sensitivity_score,
            profit_capture_consistency_score=profit_capture_consistency_score,
            data_perturbation_resilience_score=data_perturbation_resilience_score,
            overall_robustness_score=overall_robustness_score,
            robustness_classification=classification.value,
        )
        self._validator.validate_result_or_raise(result, config=scoring_config)
        return result
