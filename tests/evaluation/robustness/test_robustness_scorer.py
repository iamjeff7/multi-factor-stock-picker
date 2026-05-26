"""EntryRobustnessScorer integration tests."""

from decimal import Decimal

import pytest
from tests.evaluation.robustness.conftest import strong_robustness_inputs, weak_robustness_inputs

from core.types import ExperimentId
from evaluation.robustness.classification import classify_robustness_score
from evaluation.robustness.config import ComponentWeights, EntryRobustnessConfig
from evaluation.robustness.enums import RobustnessClassification
from evaluation.robustness.mapping import to_robustness_score_record
from evaluation.robustness.normalize import quantize_score
from evaluation.robustness.scorer import EntryRobustnessScorer
from schemas.enums import RobustnessGrade


def test_strong_signal_receives_high_overall_score() -> None:
    scorer = EntryRobustnessScorer()
    result = scorer.score(strong_robustness_inputs())

    assert result.overall_robustness_score >= Decimal("0.70")
    assert result.robustness_classification in {
        RobustnessClassification.EXCEPTIONAL.value,
        RobustnessClassification.STRONG.value,
        RobustnessClassification.GOOD.value,
    }
    for component in (
        result.ic_stability_score,
        result.return_stability_score,
        result.regime_stability_score,
        result.parameter_stability_score,
        result.rank_stability_score,
        result.breadth_stability_score,
        result.sample_stability_score,
    ):
        assert Decimal("0") <= component <= Decimal("1")


def test_weak_signal_receives_lower_score_than_strong_signal() -> None:
    scorer = EntryRobustnessScorer()
    strong = scorer.score(strong_robustness_inputs())
    weak = scorer.score(weak_robustness_inputs())

    assert weak.overall_robustness_score < strong.overall_robustness_score
    assert weak.robustness_classification in {
        RobustnessClassification.WEAK.value,
        RobustnessClassification.REJECT.value,
        RobustnessClassification.ACCEPTABLE.value,
    }


def test_overall_score_matches_weighted_sum() -> None:
    scorer = EntryRobustnessScorer()
    result = scorer.score(strong_robustness_inputs())
    weights = scorer.config.component_weights

    expected = quantize_score(
        result.ic_stability_score * weights.ic_stability
        + result.return_stability_score * weights.return_stability
        + result.regime_stability_score * weights.regime_stability
        + result.parameter_stability_score * weights.parameter_stability
        + result.rank_stability_score * weights.rank_stability
        + result.breadth_stability_score * weights.breadth_stability
        + result.sample_stability_score * weights.sample_stability
    )
    assert result.overall_robustness_score == expected


def test_invalid_component_weights_raise_validation_error() -> None:
    with pytest.raises(ValueError, match="Component weights must sum to 1.0"):
        EntryRobustnessConfig(
            component_weights=ComponentWeights(
                ic_stability=Decimal("0.50"),
                return_stability=Decimal("0.50"),
                regime_stability=Decimal("0.50"),
                parameter_stability=Decimal("0"),
                rank_stability=Decimal("0"),
                breadth_stability=Decimal("0"),
                sample_stability=Decimal("0"),
            )
        )


def test_classification_thresholds() -> None:
    thresholds = EntryRobustnessConfig().classification_thresholds
    assert (
        classify_robustness_score(Decimal("0.95"), thresholds=thresholds)
        == RobustnessClassification.EXCEPTIONAL
    )
    assert (
        classify_robustness_score(Decimal("0.45"), thresholds=thresholds)
        == RobustnessClassification.REJECT
    )


def test_mapping_to_robustness_score_record() -> None:
    scorer = EntryRobustnessScorer()
    result = scorer.score(strong_robustness_inputs(signal_id="momentum_12m"))
    record = to_robustness_score_record(
        result,
        experiment_id=ExperimentId("exp_001"),
    )

    assert record.experiment_id == ExperimentId("exp_001")
    assert record.robustness_score == result.overall_robustness_score
    assert record.stability_score == result.ic_stability_score
    assert record.overall_grade in {RobustnessGrade.A, RobustnessGrade.B, RobustnessGrade.C}


def test_reproducible_results_for_identical_inputs() -> None:
    scorer = EntryRobustnessScorer()
    inputs = strong_robustness_inputs()
    first = scorer.score(inputs)
    second = scorer.score(inputs)
    assert first == second
