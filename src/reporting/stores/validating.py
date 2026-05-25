"""Validating wrapper around result stores."""

from __future__ import annotations

from collections.abc import Sequence

from reporting.protocols import ResultStore
from reporting.validator import ResultSchemaValidator
from schemas.results import (
    BacktestSummaryRecord,
    CompositeScoreRecord,
    ConfigurationSnapshotRecord,
    EntrySignalResultRecord,
    EquityCurveRecord,
    ExitSignalResultRecord,
    ExperimentMetadata,
    ExperimentReportManifest,
    ExperimentSummaryRecord,
    FactorScoreRecord,
    PortfolioSelectionRecord,
    PortfolioSnapshotRecord,
    PositionRecord,
    RobustnessScoreRecord,
    StockSummaryRecord,
    TradeRecord,
    VersionMetadataRecord,
)


class ValidatingResultStore:
    """Validates records before delegating persistence."""

    def __init__(
        self,
        store: ResultStore,
        validator: ResultSchemaValidator | None = None,
    ) -> None:
        self._store = store
        self._validator = validator or ResultSchemaValidator()

    def create_experiment(self, metadata: ExperimentMetadata) -> None:
        self._validator.validate_experiment_metadata_or_raise(metadata)
        self._store.create_experiment(metadata)

    def save_entry_signal_results(self, rows: Sequence[EntrySignalResultRecord]) -> None:
        self._validator.validate_entry_signal_results_or_raise(rows)
        self._store.save_entry_signal_results(rows)

    def save_exit_signal_results(self, rows: Sequence[ExitSignalResultRecord]) -> None:
        self._validator.validate_exit_signal_results_or_raise(rows)
        self._store.save_exit_signal_results(rows)

    def save_factor_scores(self, rows: Sequence[FactorScoreRecord]) -> None:
        self._validator.validate_factor_scores_or_raise(rows)
        self._store.save_factor_scores(rows)

    def save_composite_scores(self, rows: Sequence[CompositeScoreRecord]) -> None:
        self._validator.validate_composite_scores_or_raise(rows)
        self._store.save_composite_scores(rows)

    def save_portfolio_selections(self, rows: Sequence[PortfolioSelectionRecord]) -> None:
        self._validator.validate_portfolio_selections_or_raise(rows)
        self._store.save_portfolio_selections(rows)

    def save_trades(self, rows: Sequence[TradeRecord]) -> None:
        self._validator.validate_trades_or_raise(rows)
        self._store.save_trades(rows)

    def save_positions(self, rows: Sequence[PositionRecord]) -> None:
        self._validator.validate_positions_or_raise(rows)
        self._store.save_positions(rows)

    def save_portfolio_snapshots(self, rows: Sequence[PortfolioSnapshotRecord]) -> None:
        self._validator.validate_portfolio_snapshots_or_raise(rows)
        self._store.save_portfolio_snapshots(rows)

    def save_equity_curve(self, rows: Sequence[EquityCurveRecord]) -> None:
        self._validator.validate_equity_curve_or_raise(rows)
        self._store.save_equity_curve(rows)

    def save_backtest_summary(self, summary: BacktestSummaryRecord) -> None:
        self._validator.validate_backtest_summary_or_raise(summary)
        self._store.save_backtest_summary(summary)

    def save_stock_summaries(self, rows: Sequence[StockSummaryRecord]) -> None:
        self._validator.validate_stock_summaries_or_raise(rows)
        self._store.save_stock_summaries(rows)

    def save_experiment_summary(self, summary: ExperimentSummaryRecord) -> None:
        self._validator.validate_experiment_summary_or_raise(summary)
        self._store.save_experiment_summary(summary)

    def save_robustness_score(self, score: RobustnessScoreRecord) -> None:
        self._validator.validate_robustness_score_or_raise(score)
        self._store.save_robustness_score(score)

    def save_configuration_snapshot(self, snapshot: ConfigurationSnapshotRecord) -> None:
        self._validator.validate_configuration_snapshot_or_raise(snapshot)
        self._store.save_configuration_snapshot(snapshot)

    def save_version_metadata(self, metadata: VersionMetadataRecord) -> None:
        self._validator.validate_version_metadata_or_raise(metadata)
        self._store.save_version_metadata(metadata)

    def save_report_manifest(self, manifest: ExperimentReportManifest) -> None:
        self._validator.validate_report_manifest_or_raise(manifest)
        self._store.save_report_manifest(manifest)

    def validate_stock_summary_matches_trades(
        self,
        trades: Sequence[TradeRecord],
        summaries: Sequence[StockSummaryRecord],
    ) -> None:
        self._validator.validate_stock_summary_matches_trades_or_raise(trades, summaries)

    @property
    def inner(self) -> ResultStore:
        return self._store
