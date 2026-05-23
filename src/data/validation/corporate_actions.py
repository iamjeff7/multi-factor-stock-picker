"""Corporate action validation."""

from __future__ import annotations

from decimal import Decimal

from schemas.data import CorporateAction, ValidationIssue


def validate_corporate_actions(
    security_id: str, actions: list[CorporateAction]
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    seen: set[tuple[str, str]] = set()

    for action in actions:
        key = (action.action_date.isoformat(), action.action_type)
        if key in seen:
            issues.append(
                ValidationIssue(
                    check_name="duplicate_corporate_action",
                    message=f"Duplicate action {action.action_type} on {action.action_date}",
                    security_id=security_id,  # type: ignore[arg-type]
                )
            )
        seen.add(key)

        if action.action_type in ("SPLIT", "REVERSE_SPLIT"):
            if action.ratio is None or action.ratio <= Decimal("0"):
                issues.append(
                    ValidationIssue(
                        check_name="invalid_split_ratio",
                        message=f"Invalid split ratio on {action.action_date}",
                        security_id=security_id,  # type: ignore[arg-type]
                    )
                )
        if action.action_type in ("CASH_DIVIDEND", "SPECIAL_DIVIDEND"):
            if action.amount is None or action.amount < Decimal("0"):
                issues.append(
                    ValidationIssue(
                        check_name="invalid_dividend_amount",
                        message=f"Invalid dividend amount on {action.action_date}",
                        security_id=security_id,  # type: ignore[arg-type]
                    )
                )

    return issues
