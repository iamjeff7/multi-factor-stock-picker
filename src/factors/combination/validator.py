"""Factor combination validation."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal

from core.exceptions import ValidationError
from core.types import SecurityId, SignalId
from entry_signals.validator import is_finite_decimal
from factors.combination.config import FactorCombinationConfig
from schemas.data import ValidationIssue, ValidationReport
from schemas.factors import CompositeScore, FactorScore


class FactorCombinationValidator:
    """Validates factor combination inputs and outputs."""

    def validate_inputs(
        self,
        factor_scores: Sequence[FactorScore],
        evaluation_date: date,
        *,
        config: FactorCombinationConfig,
    ) -> ValidationReport:
        issues: list[ValidationIssue] = []
        seen: set[tuple[SecurityId, SignalId]] = set()
        enabled_factors = set(config.enabled_factors)

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

            key = (row.security_id, row.signal_id)
            if key in seen:
                issues.append(
                    ValidationIssue(
                        check_name="duplicate_factor_score",
                        message=(
                            f"Duplicate factor score for security {row.security_id} "
                            f"and signal {row.signal_id}"
                        ),
                        security_id=row.security_id,
                    )
                )
            seen.add(key)

            if row.signal_id not in enabled_factors:
                continue

            if not is_finite_decimal(row.factor_score):
                issues.append(
                    ValidationIssue(
                        check_name="non_finite_factor_score",
                        message=f"Non-finite factor_score for {row.security_id}/{row.signal_id}",
                        security_id=row.security_id,
                    )
                )
                continue

            if (
                row.factor_score < config.score_range.min
                or row.factor_score > config.score_range.max
            ):
                issues.append(
                    ValidationIssue(
                        check_name="factor_score_out_of_range",
                        message=(
                            f"factor_score {row.factor_score} outside "
                            f"[{config.score_range.min}, {config.score_range.max}] "
                            f"for {row.security_id}/{row.signal_id}"
                        ),
                        security_id=row.security_id,
                    )
                )

        return ValidationReport(
            passed=len(issues) == 0,
            issues=issues,
            validated_at=datetime.now(tz=UTC),
        )

    def validate_outputs(
        self,
        scores: Sequence[CompositeScore],
        *,
        config: FactorCombinationConfig,
    ) -> ValidationReport:
        issues: list[ValidationIssue] = []
        seen: set[SecurityId] = set()
        ranked_rows: list[CompositeScore] = []

        for row in scores:
            if row.security_id in seen:
                issues.append(
                    ValidationIssue(
                        check_name="duplicate_security",
                        message=f"Duplicate security_id {row.security_id}",
                        security_id=row.security_id,
                    )
                )
            seen.add(row.security_id)

            if not is_finite_decimal(row.composite_score):
                issues.append(
                    ValidationIssue(
                        check_name="non_finite_composite_score",
                        message=f"Non-finite composite_score for {row.security_id}",
                        security_id=row.security_id,
                    )
                )
                continue

            if (
                row.composite_score < config.score_range.min
                or row.composite_score > config.score_range.max
            ):
                issues.append(
                    ValidationIssue(
                        check_name="composite_score_out_of_range",
                        message=(
                            f"composite_score {row.composite_score} outside "
                            f"[{config.score_range.min}, {config.score_range.max}]"
                        ),
                        security_id=row.security_id,
                    )
                )

            if row.composite_rank is None:
                continue

            ranked_rows.append(row)

            if row.factor_contributions_json is not None:
                contribution_total = _quantize(
                    sum(row.factor_contributions_json.values(), start=Decimal("0"))
                )
                if contribution_total != row.composite_score:
                    issues.append(
                        ValidationIssue(
                            check_name="contribution_total_mismatch",
                            message=(
                                f"Factor contributions sum to {contribution_total}, "
                                f"expected {row.composite_score} for {row.security_id}"
                            ),
                            security_id=row.security_id,
                        )
                    )

        if ranked_rows:
            n = Decimal(len(ranked_rows))
            for row in ranked_rows:
                if row.composite_rank is None:
                    continue
                if row.composite_rank < Decimal("1") or row.composite_rank > n:
                    issues.append(
                        ValidationIssue(
                            check_name="invalid_composite_rank",
                            message=(
                                f"Invalid composite_rank {row.composite_rank} "
                                f"for {row.security_id}"
                            ),
                            security_id=row.security_id,
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
        evaluation_date: date,
        *,
        config: FactorCombinationConfig,
    ) -> None:
        report = self.validate_inputs(factor_scores, evaluation_date, config=config)
        if not report.passed:
            raise ValidationError(_format_issues(report))

    def validate_outputs_or_raise(
        self,
        scores: Sequence[CompositeScore],
        *,
        config: FactorCombinationConfig,
    ) -> None:
        report = self.validate_outputs(scores, config=config)
        if not report.passed:
            raise ValidationError(_format_issues(report))


def _format_issues(report: ValidationReport) -> str:
    messages = "; ".join(issue.message for issue in report.issues)
    return f"Factor combination validation failed: {messages}"


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0000000001"), rounding=ROUND_HALF_UP)
