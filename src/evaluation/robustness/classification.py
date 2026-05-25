"""Robustness classification."""

from __future__ import annotations

from decimal import Decimal

from evaluation.robustness.config import ClassificationThresholds
from evaluation.robustness.enums import RobustnessClassification
from evaluation.robustness.normalize import clamp
from schemas.enums import RobustnessGrade


def classify_robustness_score(
    score: Decimal,
    *,
    thresholds: ClassificationThresholds,
) -> RobustnessClassification:
    bounded = clamp(score, Decimal("0"), Decimal("1"))
    if bounded >= thresholds.exceptional:
        return RobustnessClassification.EXCEPTIONAL
    if bounded >= thresholds.strong:
        return RobustnessClassification.STRONG
    if bounded >= thresholds.good:
        return RobustnessClassification.GOOD
    if bounded >= thresholds.acceptable:
        return RobustnessClassification.ACCEPTABLE
    if bounded >= thresholds.weak:
        return RobustnessClassification.WEAK
    return RobustnessClassification.REJECT


def classification_to_grade(classification: RobustnessClassification) -> RobustnessGrade:
    mapping = {
        RobustnessClassification.EXCEPTIONAL: RobustnessGrade.A,
        RobustnessClassification.STRONG: RobustnessGrade.B,
        RobustnessClassification.GOOD: RobustnessGrade.C,
        RobustnessClassification.ACCEPTABLE: RobustnessGrade.D,
        RobustnessClassification.WEAK: RobustnessGrade.F,
        RobustnessClassification.REJECT: RobustnessGrade.F,
    }
    return mapping[classification]
