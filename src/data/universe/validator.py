"""Universe snapshot validation."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from schemas.data import ValidationIssue, ValidationReport
from schemas.universe import UniverseMembershipSnapshot


class DefaultUniverseValidator:
    """Validates universe membership snapshots."""

    def validate(self, snapshot: UniverseMembershipSnapshot) -> ValidationReport:
        issues: list[ValidationIssue] = []
        seen: set[str] = set()

        for membership in snapshot.memberships:
            key = str(membership.security_id)
            if key in seen:
                issues.append(
                    ValidationIssue(
                        check_name="duplicate_membership",
                        message=f"Duplicate security_id {membership.security_id}",
                        security_id=membership.security_id,
                    )
                )
            seen.add(key)

            if membership.evaluation_date != snapshot.evaluation_date:
                issues.append(
                    ValidationIssue(
                        check_name="invalid_evaluation_date",
                        message=(
                            f"Membership date {membership.evaluation_date} "
                            f"!= snapshot date {snapshot.evaluation_date}"
                        ),
                        security_id=membership.security_id,
                    )
                )

            if membership.average_daily_dollar_volume is not None:
                if membership.average_daily_dollar_volume < Decimal("0"):
                    issues.append(
                        ValidationIssue(
                            check_name="negative_addv",
                            message="Negative ADDV",
                            security_id=membership.security_id,
                        )
                    )

        return ValidationReport(
            passed=len(issues) == 0,
            issues=issues,
            validated_at=datetime.now(tz=UTC),
        )
