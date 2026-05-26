"""Persist experiment reports and ranking artifacts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from experiments.metrics import DEFAULT_METRIC_WEIGHTS, PerformanceMetrics
from experiments.ranking import RankedFactor
from reporting.layout import ResultLayout
from schemas.enums import RobustnessGrade


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")
    return path


def metrics_dict(metrics: PerformanceMetrics) -> dict[str, object]:
    return {
        key: str(value) if isinstance(value, Decimal) else value
        for key, value in metrics.model_dump().items()
        if value is not None
    }


def build_rankings_payload(
    *,
    experiment_id: str,
    experiment_mode: str,
    metric_weights: dict[str, Decimal],
    segment_rankings: dict[str, list[RankedFactor]],
    thresholds: dict[str, Decimal],
) -> dict[str, object]:
    segments: dict[str, object] = {}
    for segment_key, ranked in segment_rankings.items():
        first = ranked[0] if ranked else None
        segment = first.segment.to_dict() if first else {}
        segments[segment_key] = {
            "segment": segment,
            "score_threshold": str(thresholds.get(segment_key, Decimal("0"))),
            "qualifying_percentile": 95,
            "factors": [_ranked_factor_dict(row) for row in ranked],
        }

    return {
        "experiment_id": experiment_id,
        "experiment_mode": experiment_mode,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "ranking_method": "percentile_weighted_with_robustness_penalty",
        "selection_method": "percentile_threshold_voting",
        "qualifying_percentile": 95,
        "min_qualifying_factors": 1,
        "metric_weights": {key: str(value) for key, value in metric_weights.items()},
        "segments": segments,
    }


def build_entry_report_payload(
    *,
    experiment_id: str,
    experiment_name: str,
    run_config: dict[str, object],
    execution_summary: dict[str, object],
    factor_results: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "experiment_id": experiment_id,
        "experiment_name": experiment_name,
        "experiment_mode": "entry",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "run_config": run_config,
        "execution_summary": execution_summary,
        "factor_results": factor_results,
        "rankings_artifact": "rankings/entry_top_factors.json",
        "source_artifacts": [
            "metadata/experiment.json",
            "trades/trades.parquet",
            "summaries/stock_summaries.parquet",
            "summaries/factor_summaries.parquet",
            "rankings/entry_top_factors.json",
            ResultLayout.EXPERIMENT_REPORT,
        ],
    }


def build_exit_report_payload(
    *,
    experiment_id: str,
    experiment_name: str,
    run_config: dict[str, object],
    execution_summary: dict[str, object],
    factor_results: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "experiment_id": experiment_id,
        "experiment_name": experiment_name,
        "experiment_mode": "exit",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "run_config": run_config,
        "execution_summary": execution_summary,
        "factor_results": factor_results,
        "rankings_artifact": "rankings/exit_top_factors.json",
        "source_artifacts": [
            "metadata/experiment.json",
            "trades/trades.parquet",
            "summaries/stock_summaries.parquet",
            "summaries/factor_summaries.parquet",
            "rankings/exit_top_factors.json",
            ResultLayout.EXPERIMENT_REPORT,
        ],
    }


def build_combined_report_payload(
    *,
    experiment_id: str,
    experiment_name: str,
    run_config: dict[str, object],
    execution_summary: dict[str, object],
    portfolio_metrics: dict[str, object],
    per_stock: list[dict[str, object]],
    aggregate: dict[str, object],
) -> dict[str, object]:
    return {
        "experiment_id": experiment_id,
        "experiment_name": experiment_name,
        "experiment_mode": "entry_and_exit",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "run_config": run_config,
        "execution_summary": execution_summary,
        "portfolio_metrics": portfolio_metrics,
        "per_stock": per_stock,
        "aggregate": aggregate,
        "source_artifacts": [
            "metadata/experiment.json",
            "trades/trades.parquet",
            "summaries/stock_summaries.parquet",
            "snapshots/equity_curve.parquet",
            ResultLayout.EXPERIMENT_REPORT,
        ],
    }


def _ranked_factor_dict(ranked: RankedFactor) -> dict[str, object]:
    factor = ranked.factor
    payload: dict[str, object] = {
        "rank": ranked.score_breakdown.rank,
        "signal_id": factor.signal_id,
        "variant_id": factor.variant_id,
        "final_score": str(ranked.score_breakdown.final_score),
        "selection_weight": str(ranked.selection_weight),
        "qualified": ranked.qualified,
        "score_breakdown": ranked.score_breakdown.to_dict(),
    }
    if factor.exit_horizon_months is not None:
        payload["exit_horizon_months"] = factor.exit_horizon_months
    if factor.entry_cadence is not None:
        payload["entry_cadence"] = factor.entry_cadence
    return payload


def default_metric_weights() -> dict[str, Decimal]:
    return dict(DEFAULT_METRIC_WEIGHTS)


def placeholder_robustness(grade: str = "B") -> tuple[Decimal, RobustnessGrade]:
    mapping = {
        "A": Decimal("0.85"),
        "B": Decimal("0.70"),
        "C": Decimal("0.55"),
        "D": Decimal("0.40"),
    }
    score = mapping.get(grade, Decimal("0.70"))
    return score, RobustnessGrade(grade)


def _json_default(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")
