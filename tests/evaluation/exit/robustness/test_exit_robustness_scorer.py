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
        result.performance_stability_score,
        result.regime_stability_score,
        result.parameter_stability_score,
        result.holding_period_stability_score,
        result.sample_stability_score,
        result.trade_distribution_stability_score,
        result.risk_stability_score,
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
        result.performance_stability_score * weights.performance_stability
        + result.regime_stability_score * weights.regime_stability
        + result.parameter_stability_score * weights.parameter_stability
        + result.holding_period_stability_score * weights.holding_period_stability
        + result.sample_stability_score * weights.sample_stability
        + result.trade_distribution_stability_score * weights.trade_distribution_stability
        + result.risk_stability_score * weights.risk_stability
    )
    assert result.overall_robustness_score == expected


def test_invalid_component_weights_raise_validation_error() -> None:
    with pytest.raises(ValueError, match="Component weights must sum to 1.0"):
        ExitRobustnessConfig(
            component_weights=ExitComponentWeights(
                performance_stability=Decimal("0.50"),
                regime_stability=Decimal("0.50"),
                parameter_stability=Decimal("0.50"),
                holding_period_stability=Decimal("0"),
                sample_stability=Decimal("0"),
                trade_distribution_stability=Decimal("0"),
                risk_stability=Decimal("0"),
            )
        )


def test_mapping_to_robustness_score_record() -> None:
    scorer = ExitRobustnessScorer()
    result = scorer.score(strong_exit_robustness_inputs())
    record = to_robustness_score_record(result, experiment_id=ExperimentId("exp_exit_001"))

    assert record.experiment_id == ExperimentId("exp_exit_001")
    assert record.robustness_score == result.overall_robustness_score
    assert record.stability_score == result.performance_stability_score
    assert record.overall_grade in {RobustnessGrade.A, RobustnessGrade.B, RobustnessGrade.C}


def test_reproducible_results_for_identical_inputs() -> None:
    scorer = ExitRobustnessScorer()
    inputs = strong_exit_robustness_inputs()
    assert scorer.score(inputs) == scorer.score(inputs)
