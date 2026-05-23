"""Fundamental data validation."""

from __future__ import annotations

from schemas.data import FundamentalRecord, ValidationIssue


def validate_fundamentals(
    security_id: str, records: list[FundamentalRecord]
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    seen: set[tuple[str, str]] = set()

    for record in records:
        key = (record.metric_name, record.filing_date.isoformat())
        if key in seen:
            issues.append(
                ValidationIssue(
                    check_name="duplicate_filing",
                    message=f"Duplicate filing for {record.metric_name} on {record.filing_date}",
                    security_id=security_id,  # type: ignore[arg-type]
                )
            )
        seen.add(key)

        if record.availability_date < record.filing_date:
            issues.append(
                ValidationIssue(
                    check_name="invalid_availability_date",
                    message=(
                        f"availability_date before filing_date for {record.metric_name} "
                        f"({record.availability_date} < {record.filing_date})"
                    ),
                    security_id=security_id,  # type: ignore[arg-type]
                )
            )

    return issues
