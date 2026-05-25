"""Parquet-backed result store."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from core.exceptions import ValidationError
from core.types import ExperimentId
from reporting.layout import ResultLayout
from reporting.serialization import read_record, read_records, write_record, write_records
from schemas.results import (
    BacktestSummaryRecord,
    CompositeScoreRecord,
    ConfigurationSnapshotRecord,
    EntrySignalResultRecord,
    EquityCurveRecord,
    ExitSignalResultRecord,
    ExperimentMetadata,
    ExperimentReportManifest,
    FactorScoreRecord,
    PortfolioSelectionRecord,
    PortfolioSnapshotRecord,
    PositionRecord,
    ReportArtifactRecord,
    RobustnessScoreRecord,
    StockSummaryRecord,
    TradeRecord,
    VersionMetadataRecord,
)

T = TypeVar("T", bound=BaseModel)


class ParquetResultStore:
    """Persists experiment outputs as immutable Parquet artifacts."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or ResultLayout.ROOT

    @property
    def root(self) -> Path:
        return self._root

    def experiment_path(self, experiment_id: str) -> Path:
        return self._root / experiment_id

    def create_experiment(self, metadata: ExperimentMetadata) -> None:
        experiment_dir = self.experiment_path(str(metadata.experiment_id))
        metadata_path = experiment_dir / ResultLayout.EXPERIMENT_METADATA
        if metadata_path.exists():
            raise ValidationError(
                f"Experiment already exists and is immutable: {metadata.experiment_id}"
            )
        write_record(metadata_path, metadata)

    def save_entry_signal_results(self, rows: Sequence[EntrySignalResultRecord]) -> None:
        self._write_rows(rows, ResultLayout.ENTRY_SIGNALS)

    def save_exit_signal_results(self, rows: Sequence[ExitSignalResultRecord]) -> None:
        self._write_rows(rows, ResultLayout.EXIT_SIGNALS)

    def save_factor_scores(self, rows: Sequence[FactorScoreRecord]) -> None:
        self._write_rows(rows, ResultLayout.FACTOR_SCORES)

    def save_composite_scores(self, rows: Sequence[CompositeScoreRecord]) -> None:
        self._write_rows(rows, ResultLayout.COMPOSITE_SCORES)

    def save_portfolio_selections(self, rows: Sequence[PortfolioSelectionRecord]) -> None:
        self._write_rows(rows, ResultLayout.PORTFOLIO_SELECTIONS)

    def save_trades(self, rows: Sequence[TradeRecord]) -> None:
        self._write_rows(rows, ResultLayout.TRADES_FILE)

    def save_positions(self, rows: Sequence[PositionRecord]) -> None:
        self._write_rows(rows, ResultLayout.POSITIONS_FILE)

    def save_portfolio_snapshots(self, rows: Sequence[PortfolioSnapshotRecord]) -> None:
        self._write_rows(rows, ResultLayout.PORTFOLIO_SNAPSHOTS)

    def save_equity_curve(self, rows: Sequence[EquityCurveRecord]) -> None:
        self._write_rows(rows, ResultLayout.EQUITY_CURVE)

    def save_backtest_summary(self, summary: BacktestSummaryRecord) -> None:
        self._write_single(summary, ResultLayout.BACKTEST_SUMMARY)

    def save_stock_summaries(self, rows: Sequence[StockSummaryRecord]) -> None:
        if not rows:
            return
        self._write_rows(rows, ResultLayout.STOCK_SUMMARIES)

    def save_robustness_score(self, score: RobustnessScoreRecord) -> None:
        self._write_single(score, ResultLayout.ROBUSTNESS_SCORE)

    def save_configuration_snapshot(self, snapshot: ConfigurationSnapshotRecord) -> None:
        self._write_single(snapshot, ResultLayout.CONFIGURATION_SNAPSHOT)

    def save_version_metadata(self, metadata: VersionMetadataRecord) -> None:
        self._write_single(metadata, ResultLayout.VERSION_METADATA)

    def save_report_manifest(self, manifest: ExperimentReportManifest) -> None:
        if not manifest.artifacts:
            return
        self._write_rows(manifest.artifacts, ResultLayout.REPORT_MANIFEST)

    def load_experiment_metadata(self, experiment_id: str) -> ExperimentMetadata | None:
        path = self.experiment_path(experiment_id) / ResultLayout.EXPERIMENT_METADATA
        if not path.exists():
            return None
        return read_record(path, ExperimentMetadata)

    def load_trades(self, experiment_id: str) -> list[TradeRecord]:
        return self._read_rows(experiment_id, ResultLayout.TRADES_FILE, TradeRecord)

    def load_stock_summaries(self, experiment_id: str) -> list[StockSummaryRecord]:
        return self._read_rows(experiment_id, ResultLayout.STOCK_SUMMARIES, StockSummaryRecord)

    def load_backtest_summary(self, experiment_id: str) -> BacktestSummaryRecord | None:
        path = self.experiment_path(experiment_id) / ResultLayout.BACKTEST_SUMMARY
        if not path.exists():
            return None
        return read_record(path, BacktestSummaryRecord)

    def load_report_manifest(self, experiment_id: str) -> ExperimentReportManifest | None:
        artifacts = self._read_rows(
            experiment_id,
            ResultLayout.REPORT_MANIFEST,
            ReportArtifactRecord,
        )
        if not artifacts:
            return None
        return ExperimentReportManifest(
            experiment_id=ExperimentId(experiment_id),
            artifacts=artifacts,
        )

    def _write_rows(
        self,
        rows: Sequence[object],
        relative_path: str,
    ) -> None:
        if not rows:
            return
        experiment_id = str(getattr(rows[0], "experiment_id"))
        path = self.experiment_path(experiment_id) / relative_path
        self._ensure_not_exists(path)
        write_records(path, rows)  # type: ignore[arg-type]

    def _write_single(self, row: object, relative_path: str) -> None:
        experiment_id = str(getattr(row, "experiment_id"))
        path = self.experiment_path(experiment_id) / relative_path
        self._ensure_not_exists(path)
        write_record(path, row)  # type: ignore[arg-type]

    def _read_rows(self, experiment_id: str, relative_path: str, model: type[T]) -> list[T]:
        path = self.experiment_path(experiment_id) / relative_path
        if not path.exists():
            return []
        return read_records(path, model)

    def _ensure_not_exists(self, path: Path) -> None:
        if path.exists():
            raise ValidationError(f"Result artifact already exists and is immutable: {path}")

    def _require_experiment(self, experiment_id: str) -> None:
        if self.load_experiment_metadata(experiment_id) is None:
            raise ValidationError(
                f"Experiment metadata must be created before saving results: {experiment_id}"
            )
