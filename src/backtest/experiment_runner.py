"""Cross-sectional single-factor experiment runner."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from backtest.engine import SingleStockBacktestEngine
from backtest.entry_policy import EntryPolicy, SignalPresentEntryPolicy
from backtest.experiment_config import SingleFactorExperimentConfig
from backtest.experiment_state import ExperimentRunResult, StockRunResult
from backtest.statistics import DefaultPerformanceCalculator
from core.enums import ExperimentStatus, ExperimentType
from core.exceptions import ValidationError
from core.types import ConfigurationHash, DataVersion, ExperimentId, UniverseVersion
from data.protocols import DataAccess
from entry_signals.protocols import EntrySignal
from exit_signals.protocols import ExitSignal
from reporting.aggregators import aggregate_stock_summaries
from reporting.experiment_aggregators import aggregate_experiment_summary
from reporting.generators.experiment_report import ExperimentReportGenerator
from reporting.manifest import build_backtest_report_manifest
from reporting.protocols import ResultStore
from reporting.stores import ParquetResultStore, ValidatingResultStore
from reporting.stores.validating import ValidatingResultStore as ValidatingStore
from schemas.backtest import Trade
from schemas.results import (
    BacktestSummaryRecord,
    ConfigurationSnapshotRecord,
    ExperimentMetadata,
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
        policy = entry_policy or SignalPresentEntryPolicy()
        parent_experiment_id = experiment_id or ExperimentId(f"exp_{uuid.uuid4().hex[:12]}")
        store = result_store or self._build_result_store(output_dir)

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
        )

        experiment_result = ExperimentRunResult(
            experiment_id=parent_experiment_id,
            stock_results=stock_results,
            trade_records=all_trades,
            stock_summaries=stock_summaries,
            experiment_summary=experiment_summary,
        )

        if store is not None:
            self._persist_experiment(
                store=store,
                config=config,
                data_access=data_access,
                entry_signal=entry_signal,
                exit_signal=exit_signal,
                result=experiment_result,
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
                configuration_json=config.model_dump(mode="json"),
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
        if result.stock_summaries:
            if isinstance(store, ValidatingStore):
                store.validate_stock_summary_matches_trades(
                    result.trade_records,
                    result.stock_summaries,
                )
            store.save_stock_summaries(result.stock_summaries)
        store.save_experiment_summary(result.experiment_summary)
        store.save_backtest_summary(
            BacktestSummaryRecord(
                experiment_id=result.experiment_id,
                total_return=result.experiment_summary.mean_stock_return or Decimal("0"),
                win_rate=result.experiment_summary.win_rate,
                profit_factor=result.experiment_summary.profit_factor,
                average_trade=result.experiment_summary.average_trade,
                number_of_trades=result.experiment_summary.number_of_trades,
            )
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
