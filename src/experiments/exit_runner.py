"""Exit factor evaluation experiment runner."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from core.types import ExperimentId
from data.protocols import DataAccess
from experiments.config import UnifiedExperimentConfig
from experiments.data_presets import resolve_data_preset
from experiments.enums import EntryEvaluationMode
from experiments.evaluation import UnifiedFactorEvaluator
from experiments.evaluation.summary import build_exit_evaluation_summary
from experiments.metrics import PerformanceMetrics, aggregate_metrics
from experiments.ranking import FactorVariantRef, RankCandidate, rank_factors_in_segment
from experiments.reporting import (
    build_exit_report_payload,
    build_rankings_payload,
    default_metric_weights,
    metrics_dict,
    robustness_dict,
    write_json,
)
from experiments.resolution import resolve_unified_config
from experiments.segments import SegmentClassifier, SegmentLabels
from experiments.signal_catalog import build_exit_signal, list_exit_variants
from experiments.trade_simulator import simulate_exit_factor, trades_to_metrics
from reporting.layout import ResultLayout
from schemas.backtest import Trade


class ExitExperimentRunner:
    def __init__(self, *, factor_evaluator: UnifiedFactorEvaluator | None = None) -> None:
        self._factor_evaluator = factor_evaluator or UnifiedFactorEvaluator()

    def run(
        self,
        config: UnifiedExperimentConfig,
        data_access: DataAccess,
        *,
        output_dir: Path,
        reference_date: date | None = None,
    ) -> Path:
        start_hint = config.start_date
        preset = resolve_data_preset(
            config.data_preset,
            data_access,
            [str(security.security_id) for security in config.securities],
            reference_date=reference_date,
        )
        start_date = start_hint or preset.start_date
        end_date = config.end_date or preset.end_date
        config = resolve_unified_config(config, data_access, evaluation_date=start_date)
        experiment_id = ExperimentId(f"exp_{uuid.uuid4().hex[:12]}")
        initial_capital = Decimal(str(config.initial_capital))

        classifier = SegmentClassifier()
        segment_labels_by_security: dict[str, SegmentLabels] = {}
        for security in config.securities:
            labels_map = classifier.classify_cross_section(
                data_access,
                [security.security_id],
                start_date,
            )
            segment_labels_by_security[str(security.security_id)] = labels_map[
                security.security_id
            ]

        metric_weights = default_metric_weights()
        if config.ranking.metric_weights:
            metric_weights.update(config.ranking.metric_weights)

        cadence = config.exit.entry_cadence
        factor_results: list[dict[str, object]] = []
        segment_candidates: dict[str, list[RankCandidate]] = defaultdict(list)
        segment_labels_by_key: dict[str, SegmentLabels] = {}

        for variant in list_exit_variants():
            exit_signal = build_exit_signal(variant)
            pooled_trades: list[Trade] = []
            per_stock_payload: list[dict[str, object]] = []
            stock_metrics: list[PerformanceMetrics] = []

            for security in config.securities:
                trades = simulate_exit_factor(
                    data_access=data_access,
                    security_id=security.security_id,
                    ticker=security.ticker,
                    exit_signal=exit_signal,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=initial_capital,
                    entry_mode=config.exit.entry_evaluation_mode,
                    entry_cadence=cadence,
                )
                pooled_trades.extend(trades)
                metrics = trades_to_metrics(
                    trades,
                    trading_days=preset.trading_days,
                    calendar_start=start_date,
                    calendar_end=end_date,
                    initial_capital=initial_capital,
                )
                stock_metrics.append(metrics)

            exit_robustness = self._factor_evaluator.evaluate_exit_variant(
                config=config,
                data_access=data_access,
                exit_signal=exit_signal,
                trades=pooled_trades,
                start_date=start_date,
                end_date=end_date,
                experiment_id=experiment_id,
            )
            variant_robustness = exit_robustness.robustness_score
            variant_robustness_payload = robustness_dict(
                score=variant_robustness,
                grade=exit_robustness.robustness_grade,
                available=exit_robustness.status == "completed",
            )
            evaluation_summary = build_exit_evaluation_summary(
                exit_robustness.exit_robustness_payload
            )

            for security, metrics in zip(config.securities, stock_metrics, strict=True):
                per_stock_payload.append(
                    {
                        "security_id": str(security.security_id),
                        "ticker": str(security.ticker),
                        "status": "completed",
                        "metrics": metrics_dict(metrics),
                        "robustness": variant_robustness_payload,
                    }
                )
                segment_key = segment_labels_by_security[str(security.security_id)].key()
                segment_labels_by_key[segment_key] = segment_labels_by_security[
                    str(security.security_id)
                ]
                segment_candidates[segment_key].append(
                    (
                        FactorVariantRef(
                            signal_id=variant.signal_id,
                            variant_id=variant.variant_id,
                            entry_cadence=cadence.value,
                        ),
                        metrics,
                        variant_robustness,
                        evaluation_summary,
                    )
                )

            aggregate = aggregate_metrics(stock_metrics)
            factor_results.append(
                {
                    "signal_id": variant.signal_id,
                    "variant_id": variant.variant_id,
                    "signal_version": "1.0",
                    "entry_cadence": cadence.value,
                    "exit_robustness": exit_robustness.exit_robustness_payload,
                    "per_stock": per_stock_payload,
                    "aggregate": {
                        "metrics": metrics_dict(aggregate),
                        "robustness": variant_robustness_payload,
                    },
                }
            )

        segment_rankings: dict[str, list] = {}
        thresholds: dict[str, Decimal] = {}
        for segment_key, candidates in segment_candidates.items():
            if not candidates:
                continue
            threshold, ranked = rank_factors_in_segment(
                candidates,
                segment_labels_by_key[segment_key],
                qualifying_percentile=config.ranking.qualifying_percentile,
                min_qualifying_factors=config.ranking.min_qualifying_factors,
                metric_weights=metric_weights,
            )
            segment_rankings[segment_key] = ranked
            thresholds[segment_key] = threshold

        experiment_dir = output_dir / str(experiment_id)
        rankings_payload = build_rankings_payload(
            experiment_id=str(experiment_id),
            experiment_mode="exit",
            metric_weights=metric_weights,
            segment_rankings=segment_rankings,
            thresholds=thresholds,
        )
        write_json(experiment_dir / "rankings" / "exit_top_factors.json", rankings_payload)

        run_config = {
            "data_preset": config.data_preset.value,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "trading_days": preset.trading_days,
            "universe": preset.universe_name,
            "initial_capital": str(initial_capital),
            "entry_evaluation_mode": config.exit.entry_evaluation_mode.value,
            "entry_cadence": cadence.value,
            "allow_look_ahead": (
                config.exit.entry_evaluation_mode is EntryEvaluationMode.BOTTOM_ENTRY
            ),
            "exit_robustness_enabled": config.exit.compute_robustness,
        }
        report_payload = build_exit_report_payload(
            experiment_id=str(experiment_id),
            experiment_name=config.experiment_name,
            run_config=run_config,
            execution_summary={
                "exit_signals_evaluated": len(list_exit_variants()),
                "securities_requested": len(config.securities),
                "securities_completed": len(config.securities),
                "securities_skipped": 0,
                "status": "COMPLETED",
            },
            factor_results=factor_results,
        )
        return write_json(experiment_dir / ResultLayout.EXPERIMENT_REPORT, report_payload)
