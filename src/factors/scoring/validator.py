"""Factor scoring validation."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime
from decimal import Decimal

from core.exceptions import ValidationError
from core.types import SecurityId
from entry_signals.validator import is_finite_decimal
from factors.scoring.config import FactorScoringConfig
from schemas.data import ValidationIssue, ValidationReport
from schemas.entry import EntrySignalResult
from schemas.enums import SignalDirection
from schemas.factors import FactorScore


class FactorScoringValidator:
    """Validates factor scoring inputs and outputs."""

    def validate_inputs(
        self,
        raw_signals: Sequence[EntrySignalResult],
        evaluation_date: date,
        *,
        direction: SignalDirection,
        config: FactorScoringConfig,
    ) -> ValidationReport:
        issues: list[ValidationIssue] = []
        seen: set[SecurityId] = set()

        for result in raw_signals:
            if result.evaluation_date != evaluation_date:
                issues.append(
                    ValidationIssue(
                        check_name="evaluation_date_mismatch",
                        message=(
                            f"Result date {result.evaluation_date} "
                            f"!= evaluation date {evaluation_date}"
                        ),
                        security_id=result.security_id,
                    )
                )

            if result.security_id in seen:
                issues.append(
                    ValidationIssue(
                        check_name="duplicate_security",
                        message=f"Duplicate security_id {result.security_id}",
                        security_id=result.security_id,
                    )
                )
            seen.add(result.security_id)

        if direction not in (
            SignalDirection.HIGHER_IS_BETTER,
            SignalDirection.LOWER_IS_BETTER,
        ):
            issues.append(
                ValidationIssue(
                    check_name="invalid_signal_direction",
                    message=f"Unsupported signal direction: {direction}",
                )
            )

        valid_count = sum(
            1
            for result in raw_signals
            if result.raw_signal_value is not None
            and is_finite_decimal(result.raw_signal_value)
        )
        if valid_count < config.minimum_security_count:
            issues.append(
                ValidationIssue(
                    check_name="insufficient_sample",
                    message=(
                        f"Valid observation count {valid_count} "
                        f"< minimum {config.minimum_security_count}"
                    ),
                )
            )

        return ValidationReport(
            passed=len(issues) == 0,
            issues=issues,
            validated_at=datetime.now(tz=UTC),
        )

    def validate_outputs(
        self,
        scores: Sequence[FactorScore],
        *,
        config: FactorScoringConfig,
    ) -> ValidationReport:
        issues: list[ValidationIssue] = []
        seen: set[SecurityId] = set()
        ranked_rows: list[FactorScore] = []

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

            if not is_finite_decimal(row.factor_score):
                issues.append(
                    ValidationIssue(
                        check_name="non_finite_factor_score",
                        message=f"Non-finite factor_score for {row.security_id}",
                        security_id=row.security_id,
                    )
                )
                continue

            if row.factor_score < config.score_range.min or row.factor_score > config.score_range.max:
                issues.append(
                    ValidationIssue(
                        check_name="factor_score_out_of_range",
                        message=(
                            f"factor_score {row.factor_score} outside "
                            f"[{config.score_range.min}, {config.score_range.max}]"
                        ),
                        security_id=row.security_id,
                    )
                )

            if row.factor_rank is None:
                expected = _expected_assigned_score(config)
                if expected is not None and row.factor_score != expected:
                    issues.append(
                        ValidationIssue(
                            check_name="invalid_assigned_score",
                            message=(
                                f"Expected assigned score {expected} for "
                                f"{row.security_id}, got {row.factor_score}"
                            ),
                            security_id=row.security_id,
                        )
                    )
                continue

            ranked_rows.append(row)

        if ranked_rows:
            n = Decimal(len(ranked_rows))
            for row in ranked_rows:
                if row.factor_rank is None:
                    continue
                if row.factor_rank < Decimal("1") or row.factor_rank > n:
                    issues.append(
                        ValidationIssue(
                            check_name="invalid_factor_rank",
                            message=f"Invalid factor_rank {row.factor_rank} for {row.security_id}",
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
        raw_signals: Sequence[EntrySignalResult],
        evaluation_date: date,
        *,
        direction: SignalDirection,
        config: FactorScoringConfig,
    ) -> None:
        report = self.validate_inputs(
            raw_signals,
            evaluation_date,
            direction=direction,
            config=config,
        )
        if not report.passed:
            raise ValidationError(_format_issues(report))

    def validate_outputs_or_raise(
        self,
        scores: Sequence[FactorScore],
        *,
        config: FactorScoringConfig,
    ) -> None:
        report = self.validate_outputs(scores, config=config)
        if not report.passed:
            raise ValidationError(_format_issues(report))


def is_valid_observation(raw_value: Decimal | None) -> bool:
    return raw_value is not None and is_finite_decimal(raw_value)


def _expected_assigned_score(config: FactorScoringConfig) -> Decimal | None:
    from factors.scoring.enums import ScoringMissingDataPolicy

    if config.missing_data_policy == ScoringMissingDataPolicy.ASSIGN_LOWEST_SCORE:
        return config.score_range.min
    if config.missing_data_policy == ScoringMissingDataPolicy.ASSIGN_NEUTRAL_SCORE:
        return (config.score_range.min + config.score_range.max) / Decimal("2")
    return None


def _format_issues(report: ValidationReport) -> str:
    messages = "; ".join(issue.message for issue in report.issues)
    return f"Factor scoring validation failed: {messages}"
