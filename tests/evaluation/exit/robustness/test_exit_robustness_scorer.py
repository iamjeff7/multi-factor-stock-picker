"""ExitRobustnessScorer integration tests."""

from decimal import Decimal

import pytest
from tests.evaluation.exit.robustness.conftest import (
    strong_exit_robustness_inputs,
    weak_exit_robustness_inputs,
)

from core.types import ExperimentId
from evaluation.exit.robustness.config import ExitComponentWeights, ExitRobustnessConfig
from evaluation.exit.robustness.mapping import to_robustness_score_record
from evaluation.exit.robustness.scorer import ExitRobustnessScorer
from evaluation.robustness.enums import RobustnessClassification
from evaluation.robustness.normalize import quantize_score
from schemas.enums import RobustnessGrade


def test_strong_exit_signal_receives_high_overall_score() -> None:
    scorer = ExitRobustnessScorer()
    result = scorer.score(strong_exit_robustness_inputs())

    assert result.overall_robustness_score >= Decimal("0.70")
    assert result.robustness_classification in {
        RobustnessClassification.EXCEPTIONAL.value,
        RobustnessClassification.STRONG.value,
        RobustnessClassification.GOOD.value,
    }
    for component in (
        result.trade_distribution_stability_score,
        result.holding_period_stability_score,
        result.walk_forward_stability_score,
        result.out_of_sample_retention_score,
        result.market_regime_consistency_score,
        result.parameter_sensitivity_score,
        result.profit_capture_consistency_score,
        result.data_perturbation_resilience_score,
    ):
        assert Decimal("0") <= component <= Decimal("1")


def test_weak_exit_signal_receives_lower_score_than_strong_signal() -> None:
    scorer = ExitRobustnessScorer()
    strong = scorer.score(strong_exit_robustness_inputs())
    weak = scorer.score(weak_exit_robustness_inputs())

    assert weak.overall_robustness_score < strong.overall_robustness_score


def test_overall_score_matches_weighted_sum() -> None:
    scorer = ExitRobustnessScorer()
    result = scorer.score(strong_exit_robustness_inputs())
    weights = scorer.config.component_weights

    expected = quantize_score(
        result.trade_distribution_stability_score * weights.trade_distribution_stability
        + result.holding_period_stability_score * weights.holding_period_stability
        + result.walk_forward_stability_score * weights.walk_forward_stability
        + result.out_of_sample_retention_score * weights.out_of_sample_retention
        + result.market_regime_consistency_score * weights.market_regime_consistency
        + result.parameter_sensitivity_score * weights.parameter_sensitivity
        + result.profit_capture_consistency_score * weights.profit_capture_consistency
        + result.data_perturbation_resilience_score * weights.data_perturbation_resilience
    )
    assert result.overall_robustness_score == expected


def test_invalid_component_weights_raise_validation_error() -> None:
    with pytest.raises(ValueError, match="Component weights must sum to 1.0"):
        ExitRobustnessConfig(
            component_weights=ExitComponentWeights(
                trade_distribution_stability=Decimal("0.50"),
                holding_period_stability=Decimal("0.50"),
                walk_forward_stability=Decimal("0.50"),
                out_of_sample_retention=Decimal("0"),
                market_regime_consistency=Decimal("0"),
                parameter_sensitivity=Decimal("0"),
                profit_capture_consistency=Decimal("0"),
                data_perturbation_resilience=Decimal("0"),
            )
        )


def test_mapping_to_robustness_score_record() -> None:
    scorer = ExitRobustnessScorer()
    result = scorer.score(strong_exit_robustness_inputs())
    record = to_robustness_score_record(result, experiment_id=ExperimentId("exp_exit_001"))

    assert record.experiment_id == ExperimentId("exp_exit_001")
    assert record.robustness_score == result.overall_robustness_score
    assert record.stability_score == result.walk_forward_stability_score
    assert record.overall_grade in {RobustnessGrade.A, RobustnessGrade.B, RobustnessGrade.C}


def test_reproducible_results_for_identical_inputs() -> None:
    scorer = ExitRobustnessScorer()
    inputs = strong_exit_robustness_inputs()
    assert scorer.score(inputs) == scorer.score(inputs)
