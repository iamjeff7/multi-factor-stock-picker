"""Cross-sectional multi-factor experiment runner."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from backtest.composite_entry_signal import CompositeScoreEntrySignal
from backtest.engine import SingleStockBacktestEngine
from backtest.entry_policy import EntryPolicy, SignalPresentEntryPolicy, TopNEntryPolicy
from backtest.exit_robustness import compute_partial_exit_robustness
from backtest.experiment_state import ExperimentRunResult, StockRunResult
from backtest.factor_combination_flow import (
    build_combination_result,
    score_and_combine_multi_factor,
)
from backtest.multi_factor_experiment_config import MultiFactorExperimentConfig
from backtest.portfolio_selection import build_top_n_selections_from_composite
from backtest.statistics import DefaultPerformanceCalculator
from backtest.universe_resolution import with_resolved_securities
from core.enums import ExperimentStatus, ExperimentType, SamplePeriod
from core.exceptions import ValidationError
from core.types import ConfigurationHash, DataVersion, ExperimentId, UniverseVersion
from data.protocols import DataAccess
from entry_signals.protocols import EntrySignal
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
from schemas.factors import CompositeScore
from schemas.results import (
    BacktestSummaryRecord,
    CompositeScoreRecord,
    ConfigurationSnapshotRecord,
    ExperimentMetadata,
    FactorScoreRecord,
    TradeRecord,
    VersionMetadataRecord,
)


class MultiFactorExperimentRunner:
    """Runs cross-sectional multi-factor experiments with composite ranking."""

    def __init__(
        self,
        *,
        engine: SingleStockBacktestEngine | None = None,
        performance_calculator: DefaultPerformanceCalculator | None = None,
    ) -> None:
        self._engine = engine or SingleStockBacktestEngine()
        self._performance_calculator = performance_calculator or DefaultPerformanceCalculator()
        self._report_generator = ExperimentReportGenerator()

    def run(
        self,
        config: MultiFactorExperimentConfig,
        data_access: DataAccess,
        entry_signals: list[EntrySignal],
        exit_signal: ExitSignal,
        *,
        entry_policy: EntryPolicy | None = None,
        result_store: ResultStore | None = None,
        output_dir: Path | None = None,
        experiment_id: ExperimentId | None = None,
    ) -> ExperimentRunResult:
        config = with_resolved_securities(config, data_access)
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

        cross_section = score_and_combine_multi_factor(
            config=config,
            data_access=data_access,
            entry_signals=entry_signals,
            trading_days=trading_days,
            settings=config.factor_evaluation,
        )
        factor_combination = (
            build_combination_result(
                cross_section,
                factor_signal_ids=config.entry_signal_ids(),
            )
            if cross_section is not None
            else None
        )

        if entry_policy is not None:
            policy = entry_policy
            composite_entry = CompositeScoreEntrySignal([])
        elif factor_combination is not None:
            composite_entry = CompositeScoreEntrySignal(
                factor_combination.cross_section.composite_scores
            )
            if config.top_n is not None:
                selections = build_top_n_selections_from_composite(
                    factor_combination.cross_section.composite_scores,
                    config.top_n,
                )
                policy = TopNEntryPolicy(selections)
            else:
                policy = SignalPresentEntryPolicy()
        else:
            composite_entry = CompositeScoreEntrySignal([])
            policy = SignalPresentEntryPolicy()

        stock_results, all_trades = self._run_stock_backtests(
            config=config,
            data_access=data_access,
            entry_signal=composite_entry,
            exit_signal=exit_signal,
            entry_policy=policy,
            parent_experiment_id=parent_experiment_id,
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

        exit_robustness = compute_partial_exit_robustness(
            all_trades,
            split=sample_split,
            exit_signal_id=exit_signal.metadata.signal_id,
        )

        factor_score_records = _to_factor_score_records(
            parent_experiment_id,
            cross_section.factor_scores if cross_section is not None else [],
        )
        composite_score_records = _to_composite_score_records(
            parent_experiment_id,
            cross_section.composite_scores if cross_section is not None else [],
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
            factor_combination=factor_combination,
            exit_robustness=exit_robustness,
        )

        if store is not None:
            self._persist_experiment(
                store=store,
                config=config,
                data_access=data_access,
                entry_signals=entry_signals,
                exit_signal=exit_signal,
                result=experiment_result,
                factor_score_records=factor_score_records,
                composite_score_records=composite_score_records,
                output_dir=output_dir,
            )

        return experiment_result

    def _run_stock_backtests(
        self,
        *,
        config: MultiFactorExperimentConfig,
        data_access: DataAccess,
        entry_signal: EntrySignal,
        exit_signal: ExitSignal,
        entry_policy: EntryPolicy,
        parent_experiment_id: ExperimentId,
    ) -> tuple[list[StockRunResult], list[TradeRecord]]:
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
                    entry_policy=entry_policy,
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

        return stock_results, all_trades

    def _persist_experiment(
        self,
        *,
        store: ResultStore,
        config: MultiFactorExperimentConfig,
        data_access: DataAccess,
        entry_signals: list[EntrySignal],
        exit_signal: ExitSignal,
        result: ExperimentRunResult,
        factor_score_records: list[FactorScoreRecord],
        composite_score_records: list[CompositeScoreRecord],
        output_dir: Path | None,
    ) -> None:
        config_hash = ConfigurationHash(self._configuration_hash(config))
        store.create_experiment(
            ExperimentMetadata(
                experiment_id=result.experiment_id,
                experiment_name=config.experiment_name,
                experiment_type=ExperimentType.MULTI_FACTOR,
                execution_timestamp=datetime.now(tz=UTC),
                data_version=DataVersion(str(data_access.data_version)),
                universe_version=UniverseVersion("multi_factor_cross_section"),
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
                universe_version=UniverseVersion("multi_factor_cross_section"),
                entry_signal_versions={
                    str(signal.metadata.signal_id): signal.metadata.signal_version
                    for signal in entry_signals
                },
                exit_signal_versions={
                    str(exit_signal.metadata.signal_id): exit_signal.metadata.signal_version
                },
                backtest_version="2.0.0",
            )
        )
        if result.trade_records:
            store.save_trades(result.trade_records)
        if factor_score_records:
            store.save_factor_scores(factor_score_records)
        if composite_score_records:
            store.save_composite_scores(composite_score_records)
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

    def _configuration_hash(self, config: MultiFactorExperimentConfig) -> str:
        payload = json.dumps(config.model_dump(mode="json"), sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _to_factor_score_records(
    experiment_id: ExperimentId,
    factor_scores: list,
) -> list[FactorScoreRecord]:
    return [
        FactorScoreRecord(
            experiment_id=experiment_id,
            evaluation_date=row.evaluation_date,
            security_id=row.security_id,
            ticker=row.ticker,
            signal_id=row.signal_id,
            factor_score=row.factor_score,
            factor_rank=int(row.factor_rank) if row.factor_rank is not None else None,
        )
        for row in factor_scores
    ]


def _to_composite_score_records(
    experiment_id: ExperimentId,
    composite_scores: list[CompositeScore],
) -> list[CompositeScoreRecord]:
    return [
        CompositeScoreRecord(
            experiment_id=experiment_id,
            evaluation_date=row.evaluation_date,
            security_id=row.security_id,
            ticker=row.ticker,
            composite_score=row.composite_score,
            composite_rank=_composite_rank_int(row.composite_rank),
        )
        for row in composite_scores
    ]


def _composite_rank_int(rank: Decimal | None) -> int | None:
    if rank is None:
        return None
    return int(rank.to_integral_value(rounding=ROUND_HALF_UP))
