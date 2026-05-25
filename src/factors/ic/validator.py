"""Information coefficient validation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime
from decimal import Decimal

from core.exceptions import ValidationError
from core.types import SecurityId, SignalId
from entry_signals.validator import is_finite_decimal
from factors.ic.config import ICConfig
from schemas.data import ValidationIssue, ValidationReport
from schemas.factors import FactorScore
from schemas.ic import DailyICResult, ICSummary


class ICValidator:
    """Validates IC inputs and outputs."""

    def validate_inputs(
        self,
        factor_scores: Sequence[FactorScore],
        forward_returns: Mapping[SecurityId, Decimal],
        evaluation_date: date,
        *,
        signal_id: SignalId,
        config: ICConfig,
    ) -> ValidationReport:
        issues: list[ValidationIssue] = []

        for row in factor_scores:
            if row.evaluation_date != evaluation_date:
                issues.append(
                    ValidationIssue(
                        check_name="evaluation_date_mismatch",
                        message=(
                            f"Factor score date {row.evaluation_date} "
                            f"!= evaluation date {evaluation_date}"
                        ),
                        security_id=row.security_id,
                    )
                )
            if row.signal_id != signal_id:
                issues.append(
                    ValidationIssue(
                        check_name="signal_id_mismatch",
                        message=(
                            f"Factor score signal {row.signal_id} != expected {signal_id}"
                        ),
                        security_id=row.security_id,
                    )
                )
            if not is_finite_decimal(row.factor_score):
                issues.append(
                    ValidationIssue(
                        check_name="non_finite_factor_score",
                        message=f"Non-finite factor_score for {row.security_id}",
                        security_id=row.security_id,
                    )
                )
            elif row.factor_score < Decimal("0") or row.factor_score > Decimal("1"):
                issues.append(
                    ValidationIssue(
                        check_name="factor_score_out_of_range",
                        message=f"factor_score outside [0, 1] for {row.security_id}",
                        security_id=row.security_id,
                    )
                )

        for security_id, forward_return in forward_returns.items():
            if not is_finite_decimal(forward_return):
                issues.append(
                    ValidationIssue(
                        check_name="non_finite_forward_return",
                        message=f"Non-finite forward return for {security_id}",
                        security_id=security_id,
                    )
                )

        aligned_count = _aligned_observation_count(factor_scores, forward_returns)
        if aligned_count < config.minimum_security_count:
            issues.append(
                ValidationIssue(
                    check_name="insufficient_sample",
                    message=(
                        f"Aligned observation count {aligned_count} "
                        f"< minimum {config.minimum_security_count}"
                    ),
                )
            )

        return ValidationReport(
            passed=len(issues) == 0,
            issues=issues,
            validated_at=datetime.now(tz=UTC),
        )

    def validate_daily_result(self, result: DailyICResult) -> ValidationReport:
        issues: list[ValidationIssue] = []
        if not is_finite_decimal(result.ic):
            issues.append(
                ValidationIssue(
                    check_name="non_finite_ic",
                    message=f"Non-finite IC for {result.evaluation_date}",
                )
            )
        elif result.ic < Decimal("-1") or result.ic > Decimal("1"):
            issues.append(
                ValidationIssue(
                    check_name="ic_out_of_range",
                    message=f"IC {result.ic} outside [-1, 1]",
                )
            )
        if result.security_count < 1:
            issues.append(
                ValidationIssue(
                    check_name="invalid_security_count",
                    message="security_count must be positive",
                )
            )
        return ValidationReport(
            passed=len(issues) == 0,
            issues=issues,
            validated_at=datetime.now(tz=UTC),
        )

    def validate_summary(self, summary: ICSummary) -> ValidationReport:
        issues: list[ValidationIssue] = []
        if summary.observation_count < 1:
            issues.append(
                ValidationIssue(
                    check_name="invalid_observation_count",
                    message="observation_count must be positive",
                )
            )
        if summary.hit_rate < Decimal("0") or summary.hit_rate > Decimal("1"):
            issues.append(
                ValidationIssue(
                    check_name="hit_rate_out_of_range",
                    message=f"hit_rate {summary.hit_rate} outside [0, 1]",
                )
            )
        if summary.p_value is not None and (
            summary.p_value < Decimal("0") or summary.p_value > Decimal("1")
        ):
            issues.append(
                ValidationIssue(
                    check_name="p_value_out_of_range",
                    message=f"p_value {summary.p_value} outside [0, 1]",
                )
            )
        return ValidationReport(
            passed=len(issues) == 0,
            issues=issues,
            validated_at=datetime.now(tz=UTC),
        )

    def validate_inputs_or_raise(
        self,
        factor_scores: Sequence[FactorScore],
        forward_returns: Mapping[SecurityId, Decimal],
        evaluation_date: date,
        *,
        signal_id: SignalId,
        config: ICConfig,
    ) -> None:
        report = self.validate_inputs(
            factor_scores,
            forward_returns,
            evaluation_date,
            signal_id=signal_id,
            config=config,
        )
        if not report.passed:
            raise ValidationError(_format_issues(report))

    def validate_daily_result_or_raise(self, result: DailyICResult) -> None:
        report = self.validate_daily_result(result)
        if not report.passed:
            raise ValidationError(_format_issues(report))

    def validate_summary_or_raise(self, summary: ICSummary) -> None:
        report = self.validate_summary(summary)
        if not report.passed:
            raise ValidationError(_format_issues(report))


def align_observations(
    factor_scores: Sequence[FactorScore],
    forward_returns: Mapping[SecurityId, Decimal],
) -> tuple[list[Decimal], list[Decimal], int]:
    scores: list[Decimal] = []
    returns: list[Decimal] = []
    for row in sorted(factor_scores, key=lambda item: str(item.security_id)):
        forward_return = forward_returns.get(row.security_id)
        if forward_return is None:
            continue
        if not is_finite_decimal(row.factor_score) or not is_finite_decimal(forward_return):
            continue
        scores.append(row.factor_score)
        returns.append(forward_return)
    return scores, returns, len(scores)


def _aligned_observation_count(
    factor_scores: Sequence[FactorScore],
    forward_returns: Mapping[SecurityId, Decimal],
) -> int:
    _, _, count = align_observations(factor_scores, forward_returns)
    return count


def _format_issues(report: ValidationReport) -> str:
    messages = "; ".join(issue.message for issue in report.issues)
    return f"Information coefficient validation failed: {messages}"
