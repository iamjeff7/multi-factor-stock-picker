"""Serialize cross-section factor evaluation for unified experiment reports."""

from __future__ import annotations

from backtest.exit_robustness_models import ExitRobustnessEvaluation
from backtest.factor_evaluation import FactorEvaluationResult
from reporting.factor_evaluation_payload import (
    entry_robustness_payload,
    exit_robustness_payload,
    factor_ic_payload,
    factor_performance_payload,
    factor_scoring_payload,
)


def build_cross_section_payload(
    result: FactorEvaluationResult | None,
    *,
    status: str,
    skip_reason: str | None = None,
) -> dict[str, object]:
    if result is None:
        return {
            "status": status,
            "skip_reason": skip_reason,
            "factor_scoring": None,
            "factor_ic": None,
            "factor_performance": None,
            "entry_robustness": None,
        }

    return {
        "status": status,
        "skip_reason": skip_reason,
        "factor_scoring": factor_scoring_payload(result),
        "factor_ic": factor_ic_payload(result),
        "factor_performance": factor_performance_payload(result),
        "entry_robustness": entry_robustness_payload(result),
    }


def build_exit_robustness_section_payload(
    evaluation: ExitRobustnessEvaluation | None,
    *,
    status: str,
    skip_reason: str | None = None,
) -> dict[str, object]:
    if evaluation is None:
        return {
            "status": status,
            "skip_reason": skip_reason,
            "exit_robustness": {
                "available": False,
                "pending_dimensions": [],
            },
        }

    return {
        "status": status,
        "skip_reason": skip_reason,
        "exit_robustness": exit_robustness_payload(evaluation),
    }
