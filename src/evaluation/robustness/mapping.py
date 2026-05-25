"""Map entry robustness results to persisted records."""

from __future__ import annotations

from core.types import ExperimentId
from evaluation.robustness.classification import classification_to_grade
from evaluation.robustness.enums import RobustnessClassification
from schemas.results import RobustnessScoreRecord
from schemas.robustness import EntryRobustnessResult


def to_robustness_score_record(
    result: EntryRobustnessResult,
    *,
    experiment_id: ExperimentId,
) -> RobustnessScoreRecord:
    """Map runtime robustness output to the persisted result schema."""
    classification = RobustnessClassification(result.robustness_classification)
    return RobustnessScoreRecord(
        experiment_id=experiment_id,
        robustness_score=result.overall_robustness_score,
        stability_score=result.ic_stability_score,
        consistency_score=result.sample_stability_score,
        sample_size_score=result.breadth_stability_score,
        overall_grade=classification_to_grade(classification),
    )
