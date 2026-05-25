"""Backtest integrity validation."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from backtest.state import PortfolioState
from core.exceptions import ValidationError
from schemas.data import ValidationIssue, ValidationReport


class BacktestValidator:
    """Validates portfolio state during and after a backtest."""

    def validate_state(
        self,
        state: PortfolioState,
        portfolio_value: Decimal,
        invested_capital: Decimal,
    ) -> ValidationReport:
        issues: list[ValidationIssue] = []

        if state.cash < Decimal("0"):
            issues.append(
                ValidationIssue(
                    check_name="negative_cash",
                    message=f"Negative cash balance: {state.cash}",
                )
            )

        if state.position is not None and state.position.shares < Decimal("0"):
            issues.append(
                ValidationIssue(
                    check_name="negative_shares",
                    message="Negative share count",
                    security_id=state.position.security_id,
                )
            )

        expected_value = state.cash + invested_capital
        if portfolio_value != expected_value:
            issues.append(
                ValidationIssue(
                    check_name="portfolio_value_mismatch",
                    message=(
                        f"portfolio_value {portfolio_value} != cash + invested "
                        f"{expected_value}"
                    ),
                )
            )

        return ValidationReport(
            passed=len(issues) == 0,
            issues=issues,
            validated_at=datetime.now(tz=UTC),
        )

    def validate_or_raise(
        self,
        state: PortfolioState,
        portfolio_value: Decimal,
        invested_capital: Decimal,
    ) -> None:
        report = self.validate_state(state, portfolio_value, invested_capital)
        if not report.passed:
            messages = "; ".join(issue.message for issue in report.issues)
            raise ValidationError(f"Backtest validation failed: {messages}")
