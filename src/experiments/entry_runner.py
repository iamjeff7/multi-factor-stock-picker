"""Entry factor evaluation experiment runner."""

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
from experiments.enums import ExitEvaluationMode
from experiments.metrics import PerformanceMetrics, aggregate_metrics
from experiments.ranking import FactorVariantRef, rank_factors_in_segment
from experiments.reporting import (
    build_entry_report_payload,
    build_rankings_payload,
    default_metric_weights,
    metrics_dict,
    placeholder_robustness,
    write_json,
)
from experiments.resolution import resolve_unified_config
from experiments.segments import SegmentClassifier, SegmentLabels
from experiments.signal_catalog import build_entry_signal, list_entry_variants
from experiments.trade_simulator import simulate_entry_factor, trades_to_metrics
from reporting.layout import ResultLayout


class EntryExperimentRunner:
    def run(
        self,
        config: UnifiedExperimentConfig,
        data_access: DataAccess,
        *,
        output_dir: Path,
        reference_date: date | None = None,
    ) -> Path:
        security_ids = [str(security.security_id) for security in config.securities]
        preset = resolve_data_preset(
            config.data_preset,
            data_access,
            security_ids,
            reference_date=reference_date,
        )
        start_date = config.start_date or preset.start_date
        end_date = config.end_date or preset.end_date
        config = resolve_unified_config(config, data_access, evaluation_date=start_date)
        security_ids = [str(security.security_id) for security in config.securities]
        experiment_id = ExperimentId(f"exp_{uuid.uuid4().hex[:12]}")
        initial_capital = Decimal(str(config.initial_capital))

        classifier = SegmentClassifier()
        segment_labels_by_security: dict[str, SegmentLabels] = {}
        midpoint = start_date
        for security in config.securities:
            labels_map = classifier.classify_cross_section(
                data_access,
                [security.security_id],
                midpoint,
            )
            segment_labels_by_security[str(security.security_id)] = labels_map[
                security.security_id
            ]

        metric_weights = default_metric_weights()
        if config.ranking.metric_weights:
            metric_weights.update(config.ranking.metric_weights)

        horizons = config.entry.exit_horizons_months
        factor_results: list[dict[str, object]] = []
        segment_candidates: dict[
            str, list[tuple[FactorVariantRef, PerformanceMetrics, Decimal | None]]
        ] = defaultdict(list)
        segment_labels_by_key: dict[str, SegmentLabels] = {}

        for variant in list_entry_variants():
            entry_signal = build_entry_signal(variant)
            for horizon in horizons:
                per_stock_payload: list[dict[str, object]] = []
                stock_metrics: list[PerformanceMetrics] = []
                for security in config.securities:
                    trades = simulate_entry_factor(
                        data_access=data_access,
                        security_id=security.security_id,
                        ticker=security.ticker,
                        entry_signal=entry_signal,
                        start_date=start_date,
                        end_date=end_date,
                        initial_capital=initial_capital,
                        exit_mode=config.entry.exit_evaluation_mode,
                        exit_horizon_months=horizon,
                        forward_trading_months=config.entry.forward_window_trading_months,
                    )
                    metrics = trades_to_metrics(
                        trades,
                        trading_days=preset.trading_days,
                        calendar_start=start_date,
                        calendar_end=end_date,
                        initial_capital=initial_capital,
                    )
                    stock_metrics.append(metrics)
                    robustness_score, grade = placeholder_robustness()
                    per_stock_payload.append(
                        {
                            "security_id": str(security.security_id),
                            "ticker": str(security.ticker),
                            "status": "completed",
                            "metrics": metrics_dict(metrics),
                            "robustness": {
                                "overall_robustness_score": str(robustness_score),
                                "overall_grade": grade.value,
                            },
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
                                exit_horizon_months=horizon,
                            ),
                            metrics,
                            robustness_score,
                        )
                    )

                aggregate = aggregate_metrics(stock_metrics)
                aggregate_robustness, aggregate_grade = placeholder_robustness()
                factor_results.append(
                    {
                        "signal_id": variant.signal_id,
                        "variant_id": variant.variant_id,
                        "signal_version": "1.0",
                        "exit_horizon_months": horizon,
                        "per_stock": per_stock_payload,
                        "aggregate": {
                            "metrics": metrics_dict(aggregate),
                            "robustness": {
                                "overall_robustness_score": str(aggregate_robustness),
                                "overall_grade": aggregate_grade.value,
                            },
                        },
                    }
                )

        segment_rankings: dict[str, list] = {}
        thresholds: dict[str, Decimal] = {}
        for segment_key, candidates in segment_candidates.items():
            if not candidates:
                continue
            labels = segment_labels_by_key[segment_key]
            threshold, ranked = rank_factors_in_segment(
                candidates,
                labels,
                qualifying_percentile=config.ranking.qualifying_percentile,
                min_qualifying_factors=config.ranking.min_qualifying_factors,
                metric_weights=metric_weights,
            )
            segment_rankings[segment_key] = ranked
            thresholds[segment_key] = threshold

        experiment_dir = output_dir / str(experiment_id)
        rankings_payload = build_rankings_payload(
            experiment_id=str(experiment_id),
            experiment_mode="entry",
            metric_weights=metric_weights,
            segment_rankings=segment_rankings,
            thresholds=thresholds,
        )
        write_json(experiment_dir / "rankings" / "entry_top_factors.json", rankings_payload)

        run_config = {
            "data_preset": config.data_preset.value,
            "date_resolution": preset.date_resolution.value,
            "complete_calendar_year": preset.complete_calendar_year,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "trading_days": preset.trading_days,
            "universe": preset.universe_name,
            "initial_capital": str(initial_capital),
            "exit_evaluation_mode": config.entry.exit_evaluation_mode.value,
            "exit_horizons_months": horizons,
            "allow_look_ahead": (
                config.entry.exit_evaluation_mode is ExitEvaluationMode.BEST_WITHIN_FIXED_PERIOD
            ),
        }
        report_payload = build_entry_report_payload(
            experiment_id=str(experiment_id),
            experiment_name=config.experiment_name,
            run_config=run_config,
            execution_summary={
                "entry_signals_evaluated": len(list_entry_variants()) * len(horizons),
                "securities_requested": len(config.securities),
                "securities_completed": len(config.securities),
                "securities_skipped": 0,
                "status": "COMPLETED",
            },
            factor_results=factor_results,
        )
        report_path = write_json(
            experiment_dir / ResultLayout.EXPERIMENT_REPORT,
            report_payload,
        )
        return report_path
