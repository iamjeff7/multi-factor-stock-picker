"""Cross-sectional single-factor experiment runner."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from backtest.engine import SingleStockBacktestEngine
from backtest.entry_policy import EntryPolicy, SignalPresentEntryPolicy, TopNEntryPolicy
from backtest.experiment_config import SingleFactorExperimentConfig
from backtest.experiment_state import ExperimentRunResult, StockRunResult
from backtest.factor_evaluation import SingleFactorFactorEvaluator
from backtest.portfolio_selection import build_top_n_selections
from backtest.statistics import DefaultPerformanceCalculator
from core.enums import ExperimentStatus, ExperimentType, SamplePeriod
from core.exceptions import ValidationError
from core.types import ConfigurationHash, DataVersion, ExperimentId, UniverseVersion
from data.protocols import DataAccess
from entry_signals.protocols import EntrySignal
from evaluation.robustness.mapping import to_robustness_score_record
from exit_signals.protocols import ExitSignal
from reporting.aggregators import aggregate_stock_summaries
from reporting.experiment_aggregators import (
    aggregate_experiment_summary,
    aggregate_stock_returns_from_trades,
)
from reporting.generators.experiment_report import ExperimentReportGenerator
from reporting.manifest import build_backtest_report_manifest
from reporting.protocols import ResultStore
from reporting.stores import ParquetResultStore, ValidatingResultStore
from reporting.stores.validating import ValidatingResultStore as ValidatingStore
from research.degradation import compute_degradation_metrics
from research.sample_split import (
    collect_trading_days_from_data,
    compute_sample_split,
    filter_trades_by_period,
    split_to_metadata,
)
from research.validator import validate_research_settings
from schemas.backtest import Trade
from schemas.results import (
    BacktestSummaryRecord,
    ConfigurationSnapshotRecord,
    EntrySignalResultRecord,
    ExperimentMetadata,
    FactorScoreRecord,
    TradeRecord,
    VersionMetadataRecord,
)


class SingleFactorExperimentRunner:
    """Runs isolated single-stock backtests and aggregates experiment results."""

    def __init__(
        self,
        *,
        engine: SingleStockBacktestEngine | None = None,
        report_generator: ExperimentReportGenerator | None = None,
        performance_calculator: DefaultPerformanceCalculator | None = None,
    ) -> None:
        self._engine = engine or SingleStockBacktestEngine()
        self._report_generator = report_generator or ExperimentReportGenerator()
        self._performance_calculator = performance_calculator or DefaultPerformanceCalculator()

    def run(
        self,
        config: SingleFactorExperimentConfig,
        data_access: DataAccess,
        entry_signal: EntrySignal,
        exit_signal: ExitSignal,
        *,
        entry_policy: EntryPolicy | None = None,
        result_store: ResultStore | None = None,
        output_dir: Path | None = None,
        experiment_id: ExperimentId | None = None,
    ) -> ExperimentRunResult:
        parent_experiment_id = experiment_id or ExperimentId(f"exp_{uuid.uuid4().hex[:12]}")
        store = result_store or self._build_result_store(output_dir)

        trading_days = collect_trading_days_from_data(
            data_access,
            [security.security_id for security in config.securities],
            calendar_start=config.start_date,
            calendar_end=config.end_date,
        )
        sample_split = compute_sample_split(
            trading_days,
            calendar_start=config.start_date,
            calendar_end=config.end_date,
            is_fraction=config.research.is_fraction,
        )
        validate_research_settings(
            config.research,
            start_date=config.start_date,
            end_date=config.end_date,
            split=sample_split,
        )
        split_metadata = split_to_metadata(sample_split)

        factor_evaluator = SingleFactorFactorEvaluator()
        cross_sectional_scores = None
        if entry_policy is not None:
            policy = entry_policy
        elif config.top_n is not None or config.factor_evaluation.enabled:
            cross_sectional_scores = factor_evaluator.score_cross_section(
                config=config,
                data_access=data_access,
                entry_signal=entry_signal,
                trading_days=trading_days,
                settings=config.factor_evaluation,
            )
            if config.top_n is not None:
                if cross_sectional_scores is None:
                    raise ValidationError(
                        "Cannot apply top-N entry selection without cross-sectional factor scores"
                    )
                selections = build_top_n_selections(
                    cross_sectional_scores.factor_scores,
                    config.top_n,
                )
                policy = TopNEntryPolicy(selections)
            else:
                policy = SignalPresentEntryPolicy()
        else:
            policy = SignalPresentEntryPolicy()

        stock_results: list[StockRunResult] = []
        all_trades: list[TradeRecord] = []

        for security in config.securities:
            stock_config = config.to_stock_config(security)
            try:
                engine_result = self._engine.run(
                    config=stock_config,
                    data_access=data_access,
                    entry_signal=entry_signal,
                    exit_signal=exit_signal,
                    entry_policy=policy,
                    result_store=None,
                )
            except ValidationError as exc:
                if "No trading days available" in str(exc):
                    stock_results.append(
                        StockRunResult(
                            security_id=security.security_id,
                            ticker=security.ticker,
                            status="skipped",
                            skip_reason=str(exc),
                        )
                    )
                    continue
                raise

            summary = self._performance_calculator.summarize(
                engine_result.trades,
                engine_result.equity_curve,
                Decimal(str(config.initial_capital)),
            )
            trade_records = self._to_trade_records(parent_experiment_id, engine_result.trades)
            all_trades.extend(trade_records)
            stock_summaries_for_security = aggregate_stock_summaries(trade_records)
            stock_summary = (
                stock_summaries_for_security[0] if stock_summaries_for_security else None
            )

            stock_results.append(
                StockRunResult(
                    security_id=security.security_id,
                    ticker=security.ticker,
                    status="completed",
                    total_return=summary.total_return,
                    number_of_trades=summary.number_of_trades,
                    stock_summary=stock_summary,
                )
            )

        stock_summaries = aggregate_stock_summaries(all_trades)
        stock_returns = [
            result.total_return
            for result in stock_results
            if result.status == "completed" and result.total_return is not None
        ]
        experiment_summary = aggregate_experiment_summary(
            parent_experiment_id,
            securities_requested=len(config.securities),
            securities_completed=sum(1 for row in stock_results if row.status == "completed"),
            securities_skipped=sum(1 for row in stock_results if row.status == "skipped"),
            stock_returns=stock_returns,
            trades=all_trades,
            sample_period=SamplePeriod.FULL,
        )

        completed_security_ids = [
            result.security_id for result in stock_results if result.status == "completed"
        ]
        initial_capital = Decimal(str(config.initial_capital))
        is_trades = filter_trades_by_period(
            all_trades,
            split=sample_split,
            sample_period=SamplePeriod.IN_SAMPLE,
        )
        oos_trades = filter_trades_by_period(
            all_trades,
            split=sample_split,
            sample_period=SamplePeriod.OUT_OF_SAMPLE,
        )
        is_summary = aggregate_experiment_summary(
            parent_experiment_id,
            securities_requested=len(config.securities),
            securities_completed=sum(1 for row in stock_results if row.status == "completed"),
            securities_skipped=sum(1 for row in stock_results if row.status == "skipped"),
            stock_returns=aggregate_stock_returns_from_trades(
                is_trades,
                initial_capital=initial_capital,
                security_ids=completed_security_ids,
            ),
            trades=is_trades,
            sample_period=SamplePeriod.IN_SAMPLE,
        )
        oos_summary = aggregate_experiment_summary(
            parent_experiment_id,
            securities_requested=len(config.securities),
            securities_completed=sum(1 for row in stock_results if row.status == "completed"),
            securities_skipped=sum(1 for row in stock_results if row.status == "skipped"),
            stock_returns=aggregate_stock_returns_from_trades(
                oos_trades,
                initial_capital=initial_capital,
                security_ids=completed_security_ids,
            ),
            trades=oos_trades,
            sample_period=SamplePeriod.OUT_OF_SAMPLE,
        )
        degradation = compute_degradation_metrics(is_summary, oos_summary)

        factor_evaluation, entry_signal_records, factor_score_records = (
            factor_evaluator.evaluate(
                config=config,
                data_access=data_access,
                entry_signal=entry_signal,
                trading_days=trading_days,
                split=sample_split,
                settings=config.factor_evaluation,
                experiment_id=parent_experiment_id,
                cross_sectional_scores=cross_sectional_scores,
            )
        )

        experiment_result = ExperimentRunResult(
            experiment_id=parent_experiment_id,
            stock_results=stock_results,
            trade_records=all_trades,
            stock_summaries=stock_summaries,
            experiment_summary=experiment_summary,
            sample_summaries=[is_summary, oos_summary],
            sample_split=split_metadata,
            degradation=degradation,
            factor_evaluation=factor_evaluation,
        )

        if store is not None:
            self._persist_experiment(
                store=store,
                config=config,
                data_access=data_access,
                entry_signal=entry_signal,
                exit_signal=exit_signal,
                result=experiment_result,
                entry_signal_records=entry_signal_records,
                factor_score_records=factor_score_records,
                output_dir=output_dir,
            )

        return experiment_result

    def _persist_experiment(
        self,
        *,
        store: ResultStore,
        config: SingleFactorExperimentConfig,
        data_access: DataAccess,
        entry_signal: EntrySignal,
        exit_signal: ExitSignal,
        result: ExperimentRunResult,
        entry_signal_records: list[EntrySignalResultRecord],
        factor_score_records: list[FactorScoreRecord],
        output_dir: Path | None,
    ) -> None:
        config_hash = ConfigurationHash(self._configuration_hash(config))
        store.create_experiment(
            ExperimentMetadata(
                experiment_id=result.experiment_id,
                experiment_name=config.experiment_name,
                experiment_type=ExperimentType.SINGLE_FACTOR,
                execution_timestamp=datetime.now(tz=UTC),
                data_version=DataVersion(str(data_access.data_version)),
                universe_version=UniverseVersion("single_factor_cross_section"),
                configuration_hash=config_hash,
                framework_version="2.0.0",
                status=ExperimentStatus.COMPLETED,
            )
        )
        store.save_configuration_snapshot(
            ConfigurationSnapshotRecord(
                experiment_id=result.experiment_id,
                configuration_hash=config_hash,
                configuration_json={
                    **config.model_dump(mode="json"),
                    "sample_split": result.sample_split.model_dump(mode="json")
                    if result.sample_split is not None
                    else None,
                },
            )
        )
        store.save_version_metadata(
            VersionMetadataRecord(
                experiment_id=result.experiment_id,
                framework_version="2.0.0",
                data_version=DataVersion(str(data_access.data_version)),
                universe_version=UniverseVersion("single_factor_cross_section"),
                entry_signal_versions={
                    str(entry_signal.metadata.signal_id): entry_signal.metadata.signal_version
                },
                exit_signal_versions={
                    str(exit_signal.metadata.signal_id): exit_signal.metadata.signal_version
                },
                backtest_version="2.0.0",
            )
        )
        if result.trade_records:
            store.save_trades(result.trade_records)
        if entry_signal_records:
            store.save_entry_signal_results(entry_signal_records)
        if factor_score_records:
            store.save_factor_scores(factor_score_records)
        if (
            result.factor_evaluation is not None
            and result.factor_evaluation.entry_robustness is not None
        ):
            store.save_robustness_score(
                to_robustness_score_record(
                    result.factor_evaluation.entry_robustness,
                    experiment_id=result.experiment_id,
                )
            )
        if result.stock_summaries:
            if isinstance(store, ValidatingStore):
                store.validate_stock_summary_matches_trades(
                    result.trade_records,
                    result.stock_summaries,
                )
            store.save_stock_summaries(result.stock_summaries)
        store.save_experiment_summaries(
            [result.experiment_summary, *result.sample_summaries]
        )
        store.save_backtest_summaries(
            [
                BacktestSummaryRecord(
                    experiment_id=result.experiment_id,
                    sample_period=summary.sample_period,
                    total_return=summary.mean_stock_return or Decimal("0"),
                    win_rate=summary.win_rate,
                    profit_factor=summary.profit_factor,
                    average_trade=summary.average_trade,
                    number_of_trades=summary.number_of_trades,
                )
                for summary in [result.experiment_summary, *result.sample_summaries]
            ]
        )

        report_path: Path | None = None
        if output_dir is not None:
            report_path = self._report_generator.generate(
                result,
                experiment_name=config.experiment_name,
                output_dir=output_dir,
            )
            result.report_path = str(report_path)

        store.save_report_manifest(
            build_backtest_report_manifest(
                result.experiment_id,
                has_trades=bool(result.trade_records),
                has_stock_summaries=bool(result.stock_summaries),
                has_summary=True,
                has_config=True,
                has_version=True,
                has_experiment_summary=True,
                has_experiment_report=report_path is not None,
            )
        )

    def _build_result_store(self, output_dir: Path | None) -> ResultStore | None:
        if output_dir is None:
            return None
        from reporting.validator import ResultSchemaValidator

        return ValidatingResultStore(ParquetResultStore(output_dir), ResultSchemaValidator())

    def _to_trade_records(
        self,
        experiment_id: ExperimentId,
        trades: list[Trade],
    ) -> list[TradeRecord]:
        return [
            TradeRecord(
                experiment_id=experiment_id,
                trade_id=trade.trade_id,
                security_id=trade.security_id,
                ticker=trade.ticker,
                entry_date=trade.entry_date,
                entry_price=trade.entry_price,
                exit_date=trade.exit_date,
                exit_price=trade.exit_price,
                shares=trade.shares,
                gross_pnl=trade.gross_pnl,
                net_pnl=trade.net_pnl,
                holding_days=trade.holding_days,
            )
            for trade in trades
        ]

    def _configuration_hash(self, config: SingleFactorExperimentConfig) -> str:
        payload = json.dumps(config.model_dump(mode="json"), sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]
