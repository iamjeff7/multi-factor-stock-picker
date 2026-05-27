"""Tests for evaluation summary builders."""

from experiments.evaluation.summary import (
    build_entry_evaluation_summary,
    build_exit_evaluation_summary,
)


def test_build_entry_evaluation_summary_extracts_ic_and_robustness() -> None:
    summary = build_entry_evaluation_summary(
        {
            "status": "completed",
            "factor_ic": {
                "available": True,
                "full": {"mean_ic": "0.05"},
            },
            "factor_performance": {
                "available": True,
                "full": {"mean_spread": "0.02"},
            },
            "entry_robustness": {
                "available": True,
                "overall_robustness_score": "0.71",
            },
        }
    )
    assert summary["evaluation_status"] == "completed"
    assert summary["mean_ic"] == "0.05"
    assert summary["mean_spread"] == "0.02"
    assert summary["overall_robustness_score"] == "0.71"


def test_build_exit_evaluation_summary_extracts_robustness() -> None:
    summary = build_exit_evaluation_summary(
        {
            "status": "completed",
            "exit_robustness": {
                "available": True,
                "overall_robustness_score": "0.63",
                "performance_stability_score": "0.80",
            },
        }
    )
    assert summary["evaluation_status"] == "completed"
    assert summary["overall_robustness_score"] == "0.63"
    assert summary["performance_stability_score"] == "0.80"
