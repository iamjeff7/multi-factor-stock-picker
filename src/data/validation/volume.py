"""Volume data validation."""

from __future__ import annotations

from schemas.data import PriceBar, ValidationIssue


def validate_volumes(security_id: str, bars: list[PriceBar]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for bar in bars:
        if bar.volume < 0:
            issues.append(
                ValidationIssue(
                    check_name="negative_volume",
                    message=f"Negative volume on {bar.trade_date}",
                    security_id=security_id,  # type: ignore[arg-type]
                )
            )
    return issues
