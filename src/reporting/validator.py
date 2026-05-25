"""Result schema validation before persistence."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from core.exceptions import ValidationError
from core.types import ExperimentId
from reporting.keys import (
    COMPOSITE_SCORE_PK,
    ENTRY_SIGNAL_RESULT_PK,
    EQUITY_CURVE_PK,
    EXIT_SIGNAL_RESULT_PK,
    FACTOR_SCORE_PK,
    PORTFOLIO_SELECTION_PK,
    PORTFOLIO_SNAPSHOT_PK,
    POSITION_PK,
    REPORT_ARTIFACT_PK,
    STOCK_SUMMARY_PK,
    TRADE_PK,
)
from schemas.data import ValidationIssue, ValidationReport
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


class ResultSchemaValidator:
    """Validates persisted result records before write."""

    def validate_experiment_metadata(self, metadata: ExperimentMetadata) -> ValidationReport:
        return self._report([])

    def validate_entry_signal_results(
        self,
        rows: Sequence[EntrySignalResultRecord],
    ) -> ValidationReport:
        issues = self._duplicate_key_issues(rows, ENTRY_SIGNAL_RESULT_PK, "entry_signal_result")
        for row in rows:
            issues.extend(self._finite_decimal_issues(row.raw_signal_value, "raw_signal_value"))
        return self._report(issues)

    def validate_exit_signal_results(
        self,
        rows: Sequence[ExitSignalResultRecord],
    ) -> ValidationReport:
        issues = self._duplicate_key_issues(rows, EXIT_SIGNAL_RESULT_PK, "exit_signal_result")
        return self._report(issues)

    def validate_factor_scores(self, rows: Sequence[FactorScoreRecord]) -> ValidationReport:
        issues = self._duplicate_key_issues(rows, FACTOR_SCORE_PK, "factor_score")
        for row in rows:
            issues.extend(self._finite_decimal_issues(row.factor_score, "factor_score"))
            if row.factor_score < Decimal("0") or row.factor_score > Decimal("1"):
                issues.append(
                    ValidationIssue(
                        check_name="factor_score_out_of_range",
                        message=(
                            f"factor_score {row.factor_score} outside [0, 1] "
                            f"for {row.security_id}"
                        ),
                        security_id=row.security_id,
                    )
                )
        return self._report(issues)

    def validate_composite_scores(self, rows: Sequence[CompositeScoreRecord]) -> ValidationReport:
        issues = self._duplicate_key_issues(rows, COMPOSITE_SCORE_PK, "composite_score")
        for row in rows:
            issues.extend(self._finite_decimal_issues(row.composite_score, "composite_score"))
            if row.composite_score < Decimal("0") or row.composite_score > Decimal("1"):
                issues.append(
                    ValidationIssue(
                        check_name="composite_score_out_of_range",
                        message=(
                            f"composite_score {row.composite_score} outside [0, 1] "
                            f"for {row.security_id}"
                        ),
                        security_id=row.security_id,
                    )
                )
        return self._report(issues)

    def validate_portfolio_selections(
        self,
        rows: Sequence[PortfolioSelectionRecord],
    ) -> ValidationReport:
        issues = self._duplicate_key_issues(rows, PORTFOLIO_SELECTION_PK, "portfolio_selection")
        for row in rows:
            if row.target_weight < Decimal("0"):
                issues.append(
                    ValidationIssue(
                        check_name="negative_target_weight",
                        message=f"Negative target weight for {row.security_id}",
                        security_id=row.security_id,
                    )
                )
        return self._report(issues)

    def validate_trades(self, rows: Sequence[TradeRecord]) -> ValidationReport:
        issues = self._duplicate_key_issues(rows, TRADE_PK, "trade")
        for row in rows:
            if row.shares <= Decimal("0"):
                issues.append(
                    ValidationIssue(
                        check_name="non_positive_shares",
                        message=f"Trade {row.trade_id} has non-positive shares",
                        security_id=row.security_id,
                    )
                )
            if row.exit_date is not None and row.exit_date < row.entry_date:
                issues.append(
                    ValidationIssue(
                        check_name="exit_before_entry",
                        message=f"Trade {row.trade_id} exits before entry",
                        security_id=row.security_id,
                    )
                )
            for field_name, value in (
                ("entry_price", row.entry_price),
                ("exit_price", row.exit_price),
                ("gross_pnl", row.gross_pnl),
                ("net_pnl", row.net_pnl),
                ("return_pct", row.return_pct),
            ):
                issues.extend(self._finite_decimal_issues(value, field_name))
        return self._report(issues)

    def validate_positions(self, rows: Sequence[PositionRecord]) -> ValidationReport:
        issues = self._duplicate_key_issues(rows, POSITION_PK, "position")
        for row in rows:
            if row.shares <= Decimal("0"):
                issues.append(
                    ValidationIssue(
                        check_name="non_positive_shares",
                        message=f"Position {row.position_id} has non-positive shares",
                        security_id=row.security_id,
                    )
                )
        return self._report(issues)

    def validate_portfolio_snapshots(
        self,
        rows: Sequence[PortfolioSnapshotRecord],
    ) -> ValidationReport:
        issues = self._duplicate_key_issues(rows, PORTFOLIO_SNAPSHOT_PK, "portfolio_snapshot")
        return self._report(issues)

    def validate_equity_curve(self, rows: Sequence[EquityCurveRecord]) -> ValidationReport:
        issues = self._duplicate_key_issues(rows, EQUITY_CURVE_PK, "equity_curve")
        return self._report(issues)

    def validate_backtest_summary(self, summary: BacktestSummaryRecord) -> ValidationReport:
        return self._report([])

    def validate_stock_summaries(self, rows: Sequence[StockSummaryRecord]) -> ValidationReport:
        issues = self._duplicate_key_issues(rows, STOCK_SUMMARY_PK, "stock_summary")
        for row in rows:
            if row.closed_trades + row.open_trades != row.number_of_trades:
                issues.append(
                    ValidationIssue(
                        check_name="trade_count_mismatch",
                        message=(
                            f"Stock summary for {row.security_id} has inconsistent trade counts"
                        ),
                        security_id=row.security_id,
                    )
                )
            if row.win_rate is not None and (
                row.win_rate < Decimal("0") or row.win_rate > Decimal("1")
            ):
                issues.append(
                    ValidationIssue(
                        check_name="invalid_win_rate",
                        message=f"Win rate out of range for {row.security_id}",
                        security_id=row.security_id,
                    )
                )
        return self._report(issues)

    def validate_experiment_summary(self, summary: ExperimentSummaryRecord) -> ValidationReport:
        issues: list[ValidationIssue] = []
        completed_plus_skipped = summary.securities_completed + summary.securities_skipped
        if completed_plus_skipped != summary.securities_requested:
            issues.append(
                ValidationIssue(
                    check_name="security_count_mismatch",
                    message="Completed + skipped securities != requested securities",
                )
            )
        if summary.win_rate is not None and (
            summary.win_rate < Decimal("0") or summary.win_rate > Decimal("1")
        ):
            issues.append(
                ValidationIssue(
                    check_name="invalid_win_rate",
                    message="Experiment win rate out of range",
                )
            )
        return self._report(issues)

    def validate_robustness_score(self, score: RobustnessScoreRecord) -> ValidationReport:
        issues: list[ValidationIssue] = []
        for field_name, value in (
            ("robustness_score", score.robustness_score),
            ("stability_score", score.stability_score),
            ("consistency_score", score.consistency_score),
            ("sample_size_score", score.sample_size_score),
        ):
            if value is None:
                continue
            issues.extend(self._finite_decimal_issues(value, field_name))
            if value < Decimal("0") or value > Decimal("1"):
                issues.append(
                    ValidationIssue(
                        check_name="robustness_score_out_of_range",
                        message=f"{field_name} {value} outside [0, 1]",
                    )
                )
        return self._report(issues)

    def validate_configuration_snapshot(
        self,
        snapshot: ConfigurationSnapshotRecord,
    ) -> ValidationReport:
        return self._report([])

    def validate_version_metadata(self, metadata: VersionMetadataRecord) -> ValidationReport:
        return self._report([])

    def validate_report_manifest(self, manifest: ExperimentReportManifest) -> ValidationReport:
        issues = self._duplicate_key_issues(
            manifest.artifacts,
            REPORT_ARTIFACT_PK,
            "report_artifact",
        )
        return self._report(issues)

    def validate_stock_summary_matches_trades(
        self,
        trades: Sequence[TradeRecord],
        summaries: Sequence[StockSummaryRecord],
    ) -> ValidationReport:
        issues: list[ValidationIssue] = []
        trade_counts: dict[tuple[str, str], int] = {}
        for trade in trades:
            key = (str(trade.experiment_id), str(trade.security_id))
            trade_counts[key] = trade_counts.get(key, 0) + 1

        summary_keys = {(str(row.experiment_id), str(row.security_id)) for row in summaries}
        trade_keys = set(trade_counts)
        if summary_keys != trade_keys:
            issues.append(
                ValidationIssue(
                    check_name="summary_trade_key_mismatch",
                    message="Stock summaries do not match trade security keys",
                )
            )

        for summary in summaries:
            key = (str(summary.experiment_id), str(summary.security_id))
            expected = trade_counts.get(key, 0)
            if summary.number_of_trades != expected:
                issues.append(
                    ValidationIssue(
                        check_name="summary_trade_count_mismatch",
                        message=(
                            f"Summary trade count {summary.number_of_trades} != "
                            f"expected {expected} for {summary.security_id}"
                        ),
                        security_id=summary.security_id,
                    )
                )
        return self._report(issues)

    def validate_experiment_id_consistency(
        self,
        experiment_id: ExperimentId,
        rows: Sequence[object],
    ) -> ValidationReport:
        issues: list[ValidationIssue] = []
        for row in rows:
            row_experiment_id = getattr(row, "experiment_id", None)
            if row_experiment_id is not None and row_experiment_id != experiment_id:
                issues.append(
                    ValidationIssue(
                        check_name="experiment_id_mismatch",
                        message=(
                            f"Record experiment_id {row_experiment_id} != {experiment_id}"
                        ),
                    )
                )
        return self._report(issues)

    def validate_experiment_metadata_or_raise(self, metadata: ExperimentMetadata) -> None:
        self._raise_if_failed(self.validate_experiment_metadata(metadata))

    def validate_entry_signal_results_or_raise(
        self,
        rows: Sequence[EntrySignalResultRecord],
    ) -> None:
        self._raise_if_failed(self.validate_entry_signal_results(rows))

    def validate_exit_signal_results_or_raise(
        self,
        rows: Sequence[ExitSignalResultRecord],
    ) -> None:
        self._raise_if_failed(self.validate_exit_signal_results(rows))

    def validate_factor_scores_or_raise(self, rows: Sequence[FactorScoreRecord]) -> None:
        self._raise_if_failed(self.validate_factor_scores(rows))

    def validate_composite_scores_or_raise(self, rows: Sequence[CompositeScoreRecord]) -> None:
        self._raise_if_failed(self.validate_composite_scores(rows))

    def validate_portfolio_selections_or_raise(
        self,
        rows: Sequence[PortfolioSelectionRecord],
    ) -> None:
        self._raise_if_failed(self.validate_portfolio_selections(rows))

    def validate_trades_or_raise(self, rows: Sequence[TradeRecord]) -> None:
        self._raise_if_failed(self.validate_trades(rows))

    def validate_positions_or_raise(self, rows: Sequence[PositionRecord]) -> None:
        self._raise_if_failed(self.validate_positions(rows))

    def validate_portfolio_snapshots_or_raise(
        self,
        rows: Sequence[PortfolioSnapshotRecord],
    ) -> None:
        self._raise_if_failed(self.validate_portfolio_snapshots(rows))

    def validate_equity_curve_or_raise(self, rows: Sequence[EquityCurveRecord]) -> None:
        self._raise_if_failed(self.validate_equity_curve(rows))

    def validate_backtest_summary_or_raise(self, summary: BacktestSummaryRecord) -> None:
        self._raise_if_failed(self.validate_backtest_summary(summary))

    def validate_stock_summaries_or_raise(self, rows: Sequence[StockSummaryRecord]) -> None:
        self._raise_if_failed(self.validate_stock_summaries(rows))

    def validate_experiment_summary_or_raise(self, summary: ExperimentSummaryRecord) -> None:
        self._raise_if_failed(self.validate_experiment_summary(summary))

    def validate_robustness_score_or_raise(self, score: RobustnessScoreRecord) -> None:
        self._raise_if_failed(self.validate_robustness_score(score))

    def validate_configuration_snapshot_or_raise(
        self,
        snapshot: ConfigurationSnapshotRecord,
    ) -> None:
        self._raise_if_failed(self.validate_configuration_snapshot(snapshot))

    def validate_version_metadata_or_raise(self, metadata: VersionMetadataRecord) -> None:
        self._raise_if_failed(self.validate_version_metadata(metadata))

    def validate_report_manifest_or_raise(self, manifest: ExperimentReportManifest) -> None:
        self._raise_if_failed(self.validate_report_manifest(manifest))

    def validate_stock_summary_matches_trades_or_raise(
        self,
        trades: Sequence[TradeRecord],
        summaries: Sequence[StockSummaryRecord],
    ) -> None:
        self._raise_if_failed(self.validate_stock_summary_matches_trades(trades, summaries))

    def _duplicate_key_issues(
        self,
        rows: Sequence[object],
        key_fields: tuple[str, ...],
        record_name: str,
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        seen: set[tuple[object, ...]] = set()
        for row in rows:
            key = tuple(getattr(row, field) for field in key_fields)
            if key in seen:
                issues.append(
                    ValidationIssue(
                        check_name="duplicate_primary_key",
                        message=f"Duplicate {record_name} primary key: {key}",
                    )
                )
            seen.add(key)
        return issues

    def _finite_decimal_issues(
        self,
        value: Decimal | None,
        field_name: str,
    ) -> list[ValidationIssue]:
        if value is None:
            return []
        if value.is_nan() or value.is_infinite():
            return [
                ValidationIssue(
                    check_name="non_finite_decimal",
                    message=f"Non-finite {field_name}: {value}",
                )
            ]
        return []

    def _report(self, issues: list[ValidationIssue]) -> ValidationReport:
        return ValidationReport(
            passed=len(issues) == 0,
            issues=issues,
            validated_at=datetime.now(tz=UTC),
        )

    def _raise_if_failed(self, report: ValidationReport) -> None:
        if not report.passed:
            messages = "; ".join(issue.message for issue in report.issues)
            raise ValidationError(f"Result schema validation failed: {messages}")
