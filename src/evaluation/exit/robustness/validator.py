"""Exit robustness validation."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from core.exceptions import ValidationError
from entry_signals.validator import is_finite_decimal
from evaluation.exit.robustness.config import ExitRobustnessConfig
from evaluation.robustness.normalize import quantize_score
from schemas.data import ValidationIssue, ValidationReport
from schemas.exit_robustness import ExitRobustnessInputs, ExitRobustnessResult


class ExitRobustnessValidator:
    """Validates exit robustness inputs and outputs."""

    def validate_inputs(self, inputs: ExitRobustnessInputs) -> ValidationReport:
        issues: list[ValidationIssue] = []
        required_components = (
            ("performance_stability", inputs.performance_stability),
            ("regime_stability", inputs.regime_stability),
            ("parameter_stability", inputs.parameter_stability),
            ("holding_period_stability", inputs.holding_period_stability),
            ("sample_stability", inputs.sample_stability),
            ("trade_distribution_stability", inputs.trade_distribution_stability),
            ("risk_stability", inputs.risk_stability),
        )
        for component_name, component in required_components:
            if component is None:
                issues.append(
                    ValidationIssue(
                        check_name="missing_robustness_component",
                        message=f"Missing robustness component: {component_name}",
                    )
                )
        return ValidationReport(
            passed=len(issues) == 0,
            issues=issues,
            validated_at=datetime.now(tz=UTC),
        )

    def validate_config(self, config: ExitRobustnessConfig) -> ValidationReport:
        issues: list[ValidationIssue] = []
        total_weight = (
            config.component_weights.performance_stability
            + config.component_weights.regime_stability
            + config.component_weights.parameter_stability
            + config.component_weights.holding_period_stability
            + config.component_weights.sample_stability
            + config.component_weights.trade_distribution_stability
            + config.component_weights.risk_stability
        )
        if total_weight != Decimal("1"):
            issues.append(
                ValidationIssue(
                    check_name="invalid_component_weights",
                    message=f"Component weights must sum to 1.0, got {total_weight}",
                )
            )
        return ValidationReport(
            passed=len(issues) == 0,
            issues=issues,
            validated_at=datetime.now(tz=UTC),
        )

    def validate_result(
        self,
        result: ExitRobustnessResult,
        *,
        config: ExitRobustnessConfig,
    ) -> ValidationReport:
        issues: list[ValidationIssue] = []
        component_scores = {
            "performance_stability_score": result.performance_stability_score,
            "regime_stability_score": result.regime_stability_score,
            "parameter_stability_score": result.parameter_stability_score,
            "holding_period_stability_score": result.holding_period_stability_score,
            "sample_stability_score": result.sample_stability_score,
            "trade_distribution_stability_score": result.trade_distribution_stability_score,
            "risk_stability_score": result.risk_stability_score,
            "overall_robustness_score": result.overall_robustness_score,
        }
        for field_name, value in component_scores.items():
            if not is_finite_decimal(value):
                issues.append(
                    ValidationIssue(
                        check_name="non_finite_component_score",
                        message=f"Non-finite value for {field_name}",
                    )
                )
                continue
            if value < Decimal("0") or value > Decimal("1"):
                issues.append(
                    ValidationIssue(
                        check_name="component_score_out_of_range",
                        message=f"{field_name} {value} outside [0, 1]",
                    )
                )

        expected_overall = _expected_overall_score(result, config)
        if result.overall_robustness_score != expected_overall:
            issues.append(
                ValidationIssue(
                    check_name="overall_score_mismatch",
                    message=(
                        f"overall_robustness_score {result.overall_robustness_score} "
                        f"!= expected weighted sum {expected_overall}"
                    ),
                )
            )

        return ValidationReport(
            passed=len(issues) == 0,
            issues=issues,
            validated_at=datetime.now(tz=UTC),
        )

    def validate_inputs_or_raise(self, inputs: ExitRobustnessInputs) -> None:
        report = self.validate_inputs(inputs)
        if not report.passed:
            raise ValidationError(_format_issues(report))

    def validate_config_or_raise(self, config: ExitRobustnessConfig) -> None:
        report = self.validate_config(config)
        if not report.passed:
            raise ValidationError(_format_issues(report))

    def validate_result_or_raise(
        self,
        result: ExitRobustnessResult,
        *,
        config: ExitRobustnessConfig,
    ) -> None:
        report = self.validate_result(result, config=config)
        if not report.passed:
            raise ValidationError(_format_issues(report))


def _expected_overall_score(
    result: ExitRobustnessResult,
    config: ExitRobustnessConfig,
) -> Decimal:
    weights = config.component_weights
    return quantize_score(
        result.performance_stability_score * weights.performance_stability
        + result.regime_stability_score * weights.regime_stability
        + result.parameter_stability_score * weights.parameter_stability
        + result.holding_period_stability_score * weights.holding_period_stability
        + result.sample_stability_score * weights.sample_stability
        + result.trade_distribution_stability_score * weights.trade_distribution_stability
        + result.risk_stability_score * weights.risk_stability
    )


def _format_issues(report: ValidationReport) -> str:
    messages = "; ".join(issue.message for issue in report.issues)
    return f"Exit robustness validation failed: {messages}"
