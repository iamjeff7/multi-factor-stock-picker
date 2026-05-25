"""Report manifest construction."""

from __future__ import annotations

from datetime import UTC, datetime

from core.types import ExperimentId
from reporting.layout import ResultLayout
from schemas.results import ExperimentReportManifest, ReportArtifactRecord


def build_backtest_report_manifest(
    experiment_id: ExperimentId,
    *,
    has_trades: bool,
    has_stock_summaries: bool,
    has_summary: bool,
    has_config: bool,
    has_version: bool,
    has_experiment_summary: bool = False,
    has_experiment_report: bool = False,
) -> ExperimentReportManifest:
    """Build a manifest describing persisted backtest artifacts."""
    generated_at = datetime.now(tz=UTC)
    artifacts: list[ReportArtifactRecord] = []

    if has_config:
        artifacts.append(
            _artifact(
                experiment_id,
                report_id="configuration_snapshot",
                report_type="configuration_snapshot",
                relative_path=ResultLayout.CONFIGURATION_SNAPSHOT,
                generated_at=generated_at,
            )
        )
    if has_version:
        artifacts.append(
            _artifact(
                experiment_id,
                report_id="version_metadata",
                report_type="version_metadata",
                relative_path=ResultLayout.VERSION_METADATA,
                generated_at=generated_at,
            )
        )
    if has_trades:
        artifacts.append(
            _artifact(
                experiment_id,
                report_id="trades",
                report_type="trade_log",
                relative_path=ResultLayout.TRADES_FILE,
                generated_at=generated_at,
                source_artifacts=[ResultLayout.TRADES_FILE],
            )
        )
    if has_stock_summaries:
        artifacts.append(
            _artifact(
                experiment_id,
                report_id="stock_summaries",
                report_type="stock_summary",
                relative_path=ResultLayout.STOCK_SUMMARIES,
                generated_at=generated_at,
                source_artifacts=[ResultLayout.TRADES_FILE, ResultLayout.STOCK_SUMMARIES],
            )
        )
    if has_summary:
        artifacts.append(
            _artifact(
                experiment_id,
                report_id="backtest_summary",
                report_type="backtest_summary",
                relative_path=ResultLayout.BACKTEST_SUMMARY,
                generated_at=generated_at,
                source_artifacts=[
                    ResultLayout.TRADES_FILE,
                    ResultLayout.BACKTEST_SUMMARY,
                ],
            )
        )
    if has_experiment_summary:
        artifacts.append(
            _artifact(
                experiment_id,
                report_id="experiment_summary",
                report_type="experiment_summary",
                relative_path=ResultLayout.EXPERIMENT_SUMMARY,
                generated_at=generated_at,
                source_artifacts=[
                    ResultLayout.STOCK_SUMMARIES,
                    ResultLayout.EXPERIMENT_SUMMARY,
                ],
            )
        )
    if has_experiment_report:
        artifacts.append(
            _artifact(
                experiment_id,
                report_id="experiment_report",
                report_type="experiment_report",
                relative_path=ResultLayout.EXPERIMENT_REPORT,
                generated_at=generated_at,
                format="json",
                source_artifacts=[
                    ResultLayout.TRADES_FILE,
                    ResultLayout.STOCK_SUMMARIES,
                    ResultLayout.EXPERIMENT_SUMMARY,
                    ResultLayout.EXPERIMENT_REPORT,
                ],
            )
        )

    return ExperimentReportManifest(
        experiment_id=experiment_id,
        artifacts=artifacts,
    )


def _artifact(
    experiment_id: ExperimentId,
    *,
    report_id: str,
    report_type: str,
    relative_path: str,
    generated_at: datetime,
    source_artifacts: list[str] | None = None,
    format: str = "parquet",
) -> ReportArtifactRecord:
    return ReportArtifactRecord(
        experiment_id=experiment_id,
        report_id=report_id,
        report_type=report_type,
        generated_at=generated_at,
        format=format,
        relative_path=relative_path,
        source_artifacts=source_artifacts or [relative_path],
    )
