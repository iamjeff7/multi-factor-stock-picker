"""In-memory result store for tests and example runs."""

from __future__ import annotations

from collections.abc import Sequence

from core.exceptions import ValidationError
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


class InMemoryResultStore:
    """Stores experiment outputs in memory."""

    def __init__(self) -> None:
        self.experiment: ExperimentMetadata | None = None
        self.entry_signal_results: list[EntrySignalResultRecord] = []
        self.exit_signal_results: list[ExitSignalResultRecord] = []
        self.factor_scores: list[FactorScoreRecord] = []
        self.composite_scores: list[CompositeScoreRecord] = []
        self.portfolio_selections: list[PortfolioSelectionRecord] = []
        self.trades: list[TradeRecord] = []
        self.positions: list[PositionRecord] = []
        self.snapshots: list[PortfolioSnapshotRecord] = []
        self.equity_curve: list[EquityCurveRecord] = []
        self.summary: BacktestSummaryRecord | None = None
        self.backtest_summaries: list[BacktestSummaryRecord] = []
        self.stock_summaries: list[StockSummaryRecord] = []
        self.experiment_summary: ExperimentSummaryRecord | None = None
        self.experiment_summaries: list[ExperimentSummaryRecord] = []
        self.robustness_score: RobustnessScoreRecord | None = None
        self.configuration_snapshot: ConfigurationSnapshotRecord | None = None
        self.version_metadata: VersionMetadataRecord | None = None
        self.report_manifest: ExperimentReportManifest | None = None

    def create_experiment(self, metadata: ExperimentMetadata) -> None:
        if self.experiment is not None:
            raise ValidationError(
                f"Experiment already exists: {self.experiment.experiment_id}"
            )
        self.experiment = metadata

    def save_entry_signal_results(self, rows: Sequence[EntrySignalResultRecord]) -> None:
        self._require_experiment()
        self.entry_signal_results.extend(rows)

    def save_exit_signal_results(self, rows: Sequence[ExitSignalResultRecord]) -> None:
        self._require_experiment()
        self.exit_signal_results.extend(rows)

    def save_factor_scores(self, rows: Sequence[FactorScoreRecord]) -> None:
        self._require_experiment()
        self.factor_scores.extend(rows)

    def save_composite_scores(self, rows: Sequence[CompositeScoreRecord]) -> None:
        self._require_experiment()
        self.composite_scores.extend(rows)

    def save_portfolio_selections(self, rows: Sequence[PortfolioSelectionRecord]) -> None:
        self._require_experiment()
        self.portfolio_selections.extend(rows)

    def save_trades(self, rows: Sequence[TradeRecord]) -> None:
        self._require_experiment()
        self.trades.extend(rows)

    def save_positions(self, rows: Sequence[PositionRecord]) -> None:
        self._require_experiment()
        self.positions.extend(rows)

    def save_portfolio_snapshots(self, rows: Sequence[PortfolioSnapshotRecord]) -> None:
        self._require_experiment()
        self.snapshots.extend(rows)

    def save_equity_curve(self, rows: Sequence[EquityCurveRecord]) -> None:
        self._require_experiment()
        self.equity_curve.extend(rows)

    def save_backtest_summary(self, summary: BacktestSummaryRecord) -> None:
        self.save_backtest_summaries([summary])

    def save_backtest_summaries(self, summaries: Sequence[BacktestSummaryRecord]) -> None:
        self._require_experiment()
        if self.backtest_summaries:
            raise ValidationError("Backtest summaries already persisted")
        self.backtest_summaries.extend(summaries)
        full = next(
            (row for row in summaries if row.sample_period.value == "FULL"),
            summaries[0] if summaries else None,
        )
        self.summary = full

    def save_stock_summaries(self, rows: Sequence[StockSummaryRecord]) -> None:
        self._require_experiment()
        if self.stock_summaries:
            raise ValidationError("Stock summaries already persisted")
        self.stock_summaries.extend(rows)

    def save_experiment_summary(self, summary: ExperimentSummaryRecord) -> None:
        self.save_experiment_summaries([summary])

    def save_experiment_summaries(self, summaries: Sequence[ExperimentSummaryRecord]) -> None:
        self._require_experiment()
        if self.experiment_summaries:
            raise ValidationError("Experiment summaries already persisted")
        self.experiment_summaries.extend(summaries)
        full = next(
            (row for row in summaries if row.sample_period.value == "FULL"),
            summaries[0] if summaries else None,
        )
        self.experiment_summary = full

    def save_robustness_score(self, score: RobustnessScoreRecord) -> None:
        self._require_experiment()
        if self.robustness_score is not None:
            raise ValidationError("Robustness score already persisted")
        self.robustness_score = score

    def save_configuration_snapshot(self, snapshot: ConfigurationSnapshotRecord) -> None:
        self._require_experiment()
        if self.configuration_snapshot is not None:
            raise ValidationError("Configuration snapshot already persisted")
        self.configuration_snapshot = snapshot

    def save_version_metadata(self, metadata: VersionMetadataRecord) -> None:
        self._require_experiment()
        if self.version_metadata is not None:
            raise ValidationError("Version metadata already persisted")
        self.version_metadata = metadata

    def save_report_manifest(self, manifest: ExperimentReportManifest) -> None:
        self._require_experiment()
        if self.report_manifest is not None:
            raise ValidationError("Report manifest already persisted")
        self.report_manifest = manifest

    def _require_experiment(self) -> None:
        if self.experiment is None:
            raise ValidationError("Experiment metadata must be created before saving results")
