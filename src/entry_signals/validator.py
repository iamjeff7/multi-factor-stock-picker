"""Entry signal validation."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime
from decimal import Decimal

from core.exceptions import ValidationError
from core.types import SecurityId
from schemas.data import ValidationIssue, ValidationReport
from schemas.entry import EntrySignalResult, SignalMetadata
from schemas.universe import UniverseMembershipSnapshot


class EntrySignalValidator:
    """Validates entry signal inputs and outputs."""

    def validate_inputs(
        self,
        evaluation_date: date,
        universe: UniverseMembershipSnapshot,
        metadata: SignalMetadata,
    ) -> ValidationReport:
        issues: list[ValidationIssue] = []

        if universe.evaluation_date != evaluation_date:
            issues.append(
                ValidationIssue(
                    check_name="evaluation_date_mismatch",
                    message=(
                        f"Universe date {universe.evaluation_date} "
                        f"!= evaluation date {evaluation_date}"
                    ),
                )
            )

        if not any(m.is_member for m in universe.memberships):
            issues.append(
                ValidationIssue(
                    check_name="empty_universe",
                    message="Universe snapshot has no eligible members",
                )
            )

        if metadata.signal_id is None:
            issues.append(
                ValidationIssue(
                    check_name="missing_signal_id",
                    message="Signal metadata missing signal_id",
                )
            )

        return ValidationReport(
            passed=len(issues) == 0,
            issues=issues,
            validated_at=datetime.now(tz=UTC),
        )

    def validate_results(self, results: Sequence[EntrySignalResult]) -> ValidationReport:
        issues: list[ValidationIssue] = []
        seen: set[tuple[SecurityId, str]] = set()

        for result in results:
            key = (result.security_id, str(result.signal_id))
            if key in seen:
                issues.append(
                    ValidationIssue(
                        check_name="duplicate_result",
                        message=(
                            f"Duplicate result for security {result.security_id} "
                            f"and signal {result.signal_id}"
                        ),
                        security_id=result.security_id,
                    )
                )
            seen.add(key)

            if result.raw_signal_value is not None and not is_finite_decimal(
                result.raw_signal_value
            ):
                issues.append(
                    ValidationIssue(
                        check_name="non_finite_value",
                        message=f"Non-finite raw_signal_value for {result.security_id}",
                        security_id=result.security_id,
                    )
                )

        return ValidationReport(
            passed=len(issues) == 0,
            issues=issues,
            validated_at=datetime.now(tz=UTC),
        )

    def validate_inputs_or_raise(
        self,
        evaluation_date: date,
        universe: UniverseMembershipSnapshot,
        metadata: SignalMetadata,
    ) -> None:
        report = self.validate_inputs(evaluation_date, universe, metadata)
        if not report.passed:
            raise ValidationError(_format_issues(report))

    def validate_results_or_raise(self, results: Sequence[EntrySignalResult]) -> None:
        report = self.validate_results(results)
        if not report.passed:
            raise ValidationError(_format_issues(report))


def is_finite_decimal(value: Decimal) -> bool:
    if value.is_nan() or value.is_infinite():
        return False
    return True


def _format_issues(report: ValidationReport) -> str:
    messages = "; ".join(issue.message for issue in report.issues)
    return f"Entry signal validation failed: {messages}"
