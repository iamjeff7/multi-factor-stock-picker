"""Exit signal validation."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from core.exceptions import ValidationError
from schemas.data import ValidationIssue, ValidationReport
from schemas.enums import ExitDecision
from schemas.exit import ExitSignalResult, PositionContext


class ExitSignalValidator:
    """Validates exit signal inputs and outputs."""

    def validate_inputs(
        self,
        evaluation_date: date,
        position: PositionContext,
    ) -> ValidationReport:
        issues: list[ValidationIssue] = []

        if evaluation_date < position.entry_date:
            issues.append(
                ValidationIssue(
                    check_name="evaluation_before_entry",
                    message=(
                        f"Evaluation date {evaluation_date} is before "
                        f"entry date {position.entry_date}"
                    ),
                    security_id=position.security_id,
                )
            )

        if position.entry_price <= Decimal("0"):
            issues.append(
                ValidationIssue(
                    check_name="invalid_entry_price",
                    message="Entry price must be positive",
                    security_id=position.security_id,
                )
            )

        if position.holding_period < 0:
            issues.append(
                ValidationIssue(
                    check_name="invalid_holding_period",
                    message="Holding period must be non-negative",
                    security_id=position.security_id,
                )
            )

        return ValidationReport(
            passed=len(issues) == 0,
            issues=issues,
            validated_at=datetime.now(tz=UTC),
        )

    def validate_result(self, result: ExitSignalResult) -> ValidationReport:
        issues: list[ValidationIssue] = []

        if result.decision not in {ExitDecision.EXIT, ExitDecision.HOLD}:
            issues.append(
                ValidationIssue(
                    check_name="invalid_decision",
                    message=f"Invalid exit decision: {result.decision}",
                    security_id=result.security_id,
                )
            )

        if result.decision is ExitDecision.EXIT and not result.trigger_reason:
            issues.append(
                ValidationIssue(
                    check_name="missing_trigger_reason",
                    message="EXIT decision requires trigger_reason",
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
        position: PositionContext,
    ) -> None:
        report = self.validate_inputs(evaluation_date, position)
        if not report.passed:
            raise ValidationError(_format_issues(report))

    def validate_result_or_raise(self, result: ExitSignalResult) -> None:
        report = self.validate_result(result)
        if not report.passed:
            raise ValidationError(_format_issues(report))


def _format_issues(report: ValidationReport) -> str:
    messages = "; ".join(issue.message for issue in report.issues)
    return f"Exit signal validation failed: {messages}"
