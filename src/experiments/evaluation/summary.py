"""Compact evaluation summaries for unified experiment rankings."""

from __future__ import annotations

from typing import Any


def build_entry_evaluation_summary(cross_section_payload: dict[str, object]) -> dict[str, object]:
    factor_ic = _as_dict(cross_section_payload.get("factor_ic"))
    factor_performance = _as_dict(cross_section_payload.get("factor_performance"))
    entry_robustness = _as_dict(cross_section_payload.get("entry_robustness"))

    ic_summary = _as_dict(factor_ic.get("full")) if factor_ic.get("available") else {}
    if not ic_summary and factor_ic.get("sample_metrics"):
        sample_metrics = _as_dict(factor_ic.get("sample_metrics"))
        ic_summary = next(iter(sample_metrics.values()), {})

    performance_summary = _as_dict(factor_performance.get("full"))
    if not performance_summary and factor_performance.get("sample_metrics"):
        sample_metrics = _as_dict(factor_performance.get("sample_metrics"))
        performance_summary = next(iter(sample_metrics.values()), {})

    return {
        "evaluation_status": cross_section_payload.get("status"),
        "mean_ic": ic_summary.get("mean_ic"),
        "mean_spread": performance_summary.get("mean_spread"),
        "overall_robustness_score": entry_robustness.get("overall_robustness_score"),
    }


def build_exit_evaluation_summary(exit_robustness_payload: dict[str, object]) -> dict[str, object]:
    exit_robustness = _as_dict(exit_robustness_payload.get("exit_robustness"))
    return {
        "evaluation_status": exit_robustness_payload.get("status"),
        "overall_robustness_score": exit_robustness.get("overall_robustness_score"),
        "walk_forward_stability_score": exit_robustness.get("walk_forward_stability_score"),
    }


def _as_dict(value: Any) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    return {}
