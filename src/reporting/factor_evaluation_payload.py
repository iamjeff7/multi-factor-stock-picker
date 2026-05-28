"""Shared factor and robustness report section builders."""

from __future__ import annotations

from backtest.exit_robustness_models import ExitRobustnessEvaluation
from backtest.factor_evaluation import FactorEvaluationResult
from schemas.performance import FactorPerformanceSampleAnalysis


def factor_scoring_payload(factor_evaluation: FactorEvaluationResult) -> dict[str, object]:
    summary = factor_evaluation.scoring_summary
    return {
        "signal_id": str(summary.signal_id),
        "evaluation_dates": summary.evaluation_dates,
        "total_scores": summary.total_scores,
        "securities_per_date": summary.securities_per_date,
        "skipped_dates": factor_evaluation.skipped_dates,
    }


def factor_ic_payload(factor_evaluation: FactorEvaluationResult) -> dict[str, object] | None:
    analysis = factor_evaluation.ic_analysis
    if analysis is None and factor_evaluation.full_ic_summary is None:
        return {
            "signal_id": str(factor_evaluation.signal_id),
            "horizon": factor_evaluation.horizon,
            "daily_ic_count": factor_evaluation.daily_ic_count,
            "available": False,
        }

    payload: dict[str, object] = {
        "signal_id": str(factor_evaluation.signal_id),
        "horizon": factor_evaluation.horizon,
        "daily_ic_count": factor_evaluation.daily_ic_count,
        "available": True,
    }
    if analysis is not None:
        if analysis.full_summary is not None:
            payload["full"] = analysis.full_summary.model_dump(mode="json")
        payload["sample_metrics"] = {
            analysis.in_sample_summary.sample_period.value: analysis.in_sample_summary.model_dump(
                mode="json"
            ),
            analysis.out_of_sample_summary.sample_period.value: (
                analysis.out_of_sample_summary.model_dump(mode="json")
            ),
        }
        payload["is_to_oos_degradation"] = analysis.degradation.model_dump(mode="json")
    elif factor_evaluation.full_ic_summary is not None:
        payload["full"] = factor_evaluation.full_ic_summary.model_dump(mode="json")
        payload["sample_metrics"] = None
        payload["is_to_oos_degradation"] = None
    return payload


def entry_robustness_payload(factor_evaluation: FactorEvaluationResult) -> dict[str, object]:
    robustness = factor_evaluation.entry_robustness
    if robustness is None:
        return {
            "signal_id": str(factor_evaluation.signal_id),
            "available": False,
            "pending_dimensions": factor_evaluation.robustness_pending_dimensions,
        }

    return {
        "signal_id": str(robustness.signal_id),
        "available": True,
        "overall_robustness_score": str(robustness.overall_robustness_score),
        "robustness_classification": robustness.robustness_classification,
        "ic_stability_score": str(robustness.ic_stability_score),
        "return_stability_score": str(robustness.return_stability_score),
        "walk_forward_stability_score": str(robustness.walk_forward_stability_score),
        "out_of_sample_retention_score": str(robustness.out_of_sample_retention_score),
        "market_regime_consistency_score": str(robustness.market_regime_consistency_score),
        "parameter_sensitivity_score": str(robustness.parameter_sensitivity_score),
        "factor_decay_resistance_score": str(robustness.factor_decay_resistance_score),
        "data_perturbation_resilience_score": str(robustness.data_perturbation_resilience_score),
        "pending_dimensions": factor_evaluation.robustness_pending_dimensions,
    }


def factor_performance_payload(
    factor_evaluation: FactorEvaluationResult,
) -> dict[str, object]:
    performance = factor_evaluation.factor_performance
    if performance is None:
        return {
            "signal_id": str(factor_evaluation.signal_id),
            "horizon": factor_evaluation.horizon,
            "available": False,
        }

    if isinstance(performance, FactorPerformanceSampleAnalysis):
        payload: dict[str, object] = {
            "signal_id": str(performance.signal_id),
            "horizon": performance.horizon,
            "available": True,
        }
        if performance.full_summary is not None:
            payload["full"] = performance.full_summary.model_dump(mode="json")
        payload["sample_metrics"] = {
            performance.in_sample_summary.sample_period.value: (
                performance.in_sample_summary.model_dump(mode="json")
            ),
            performance.out_of_sample_summary.sample_period.value: (
                performance.out_of_sample_summary.model_dump(mode="json")
            ),
        }
        return payload

    return {
        "signal_id": str(performance.signal_id),
        "horizon": performance.horizon,
        "available": True,
        "full": performance.model_dump(mode="json"),
        "sample_metrics": None,
    }


def exit_robustness_payload(exit_robustness: ExitRobustnessEvaluation) -> dict[str, object]:
    result = exit_robustness.result
    if result is None:
        return {
            "exit_signal_id": str(exit_robustness.exit_signal_id),
            "available": False,
            "pending_dimensions": exit_robustness.pending_dimensions,
        }

    return {
        "exit_signal_id": str(result.exit_signal_id),
        "available": True,
        "overall_robustness_score": str(result.overall_robustness_score),
        "robustness_classification": result.robustness_classification,
        "trade_distribution_stability_score": str(result.trade_distribution_stability_score),
        "holding_period_stability_score": str(result.holding_period_stability_score),
        "walk_forward_stability_score": str(result.walk_forward_stability_score),
        "out_of_sample_retention_score": str(result.out_of_sample_retention_score),
        "market_regime_consistency_score": str(result.market_regime_consistency_score),
        "parameter_sensitivity_score": str(result.parameter_sensitivity_score),
        "profit_capture_consistency_score": str(result.profit_capture_consistency_score),
        "data_perturbation_resilience_score": str(result.data_perturbation_resilience_score),
        "pending_dimensions": exit_robustness.pending_dimensions,
    }
