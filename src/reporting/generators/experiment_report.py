"""Experiment report generation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from backtest.experiment_state import ExperimentRunResult, StockRunResult
from backtest.factor_evaluation import FactorEvaluationResult
from reporting.layout import ResultLayout
from schemas.performance import FactorPerformanceSampleAnalysis
from schemas.results import ExperimentSummaryRecord, StockSummaryRecord, TradeRecord


class ExperimentReportGenerator:
    """Writes the final experiment report artifact."""

    def generate(
        self,
        result: ExperimentRunResult,
        *,
        experiment_name: str,
        output_dir: Path,
    ) -> Path:
        report_path = (
            output_dir
            / str(result.experiment_id)
            / ResultLayout.EXPERIMENT_REPORT
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)

        payload = build_experiment_report_payload(
            result=result,
            experiment_name=experiment_name,
        )
        report_path.write_text(
            json.dumps(payload, indent=2, default=_json_default),
            encoding="utf-8",
        )
        return report_path


def build_experiment_report_payload(
    *,
    result: ExperimentRunResult,
    experiment_name: str,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "experiment_id": str(result.experiment_id),
        "experiment_name": experiment_name,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "trade_metrics": _trade_metrics(result.trade_records),
        "stock_metrics": [_stock_metric(row) for row in result.stock_summaries],
        "experiment_metrics": _experiment_metrics(result.experiment_summary),
        "stock_runs": [_stock_run(row) for row in result.stock_results],
        "source_artifacts": [
            ResultLayout.TRADES_FILE,
            ResultLayout.STOCK_SUMMARIES,
            ResultLayout.EXPERIMENT_SUMMARY,
            ResultLayout.BACKTEST_SUMMARY,
            ResultLayout.EXPERIMENT_REPORT,
        ],
    }
    if result.sample_split is not None:
        payload["sample_split"] = result.sample_split.model_dump(mode="json")
    if result.sample_summaries:
        payload["sample_metrics"] = {
            summary.sample_period.value: _experiment_metrics(summary)
            for summary in result.sample_summaries
        }
    if result.degradation is not None:
        payload["is_to_oos_degradation"] = result.degradation.model_dump(mode="json")
    if result.factor_evaluation is not None:
        payload["factor_scoring"] = _factor_scoring_payload(result.factor_evaluation)
        payload["factor_ic"] = _factor_ic_payload(result.factor_evaluation)
        payload["entry_robustness"] = _entry_robustness_payload(result.factor_evaluation)
        payload["factor_performance"] = _factor_performance_payload(result.factor_evaluation)
    return payload


def _factor_scoring_payload(factor_evaluation: FactorEvaluationResult) -> dict[str, object]:
    summary = factor_evaluation.scoring_summary
    return {
        "signal_id": str(summary.signal_id),
        "evaluation_dates": summary.evaluation_dates,
        "total_scores": summary.total_scores,
        "securities_per_date": summary.securities_per_date,
        "skipped_dates": factor_evaluation.skipped_dates,
    }


def _factor_ic_payload(factor_evaluation: FactorEvaluationResult) -> dict[str, object] | None:
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


def _entry_robustness_payload(factor_evaluation: FactorEvaluationResult) -> dict[str, object]:
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
        "sample_stability_score": str(robustness.sample_stability_score),
        "rank_stability_score": str(robustness.rank_stability_score),
        "parameter_stability_score": str(robustness.parameter_stability_score),
        "pending_dimensions": factor_evaluation.robustness_pending_dimensions,
    }


def _factor_performance_payload(
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


def _trade_metrics(trades: list[TradeRecord]) -> dict[str, object]:
    closed = [trade for trade in trades if trade.exit_date is not None]
    winners = [trade for trade in closed if (trade.net_pnl or Decimal("0")) > 0]
    total_net_pnl = sum(
        ((trade.net_pnl or Decimal("0")) for trade in closed),
        Decimal("0"),
    )
    return {
        "number_of_trades": len(closed),
        "win_rate": str(len(winners) / len(closed)) if closed else None,
        "total_net_pnl": str(total_net_pnl) if closed else None,
    }


def _stock_metric(summary: StockSummaryRecord) -> dict[str, object]:
    return summary.model_dump(mode="json")


def _experiment_metrics(summary: ExperimentSummaryRecord) -> dict[str, object]:
    return summary.model_dump(mode="json")


def _stock_run(result: StockRunResult) -> dict[str, object]:
    return {
        "security_id": str(result.security_id),
        "ticker": str(result.ticker),
        "status": result.status,
        "skip_reason": result.skip_reason,
        "total_return": str(result.total_return) if result.total_return is not None else None,
        "number_of_trades": result.number_of_trades,
    }


def _json_default(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")
