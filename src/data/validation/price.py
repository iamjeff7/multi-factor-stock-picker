"""Price data validation."""

from __future__ import annotations

from datetime import date

from schemas.data import PriceBar, ValidationIssue


def validate_prices(security_id: str, bars: list[PriceBar]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    seen_dates: set[date] = set()

    for bar in bars:
        if bar.trade_date in seen_dates:
            issues.append(
                ValidationIssue(
                    check_name="duplicate_price_date",
                    message=f"Duplicate trade_date {bar.trade_date}",
                    security_id=security_id,  # type: ignore[arg-type]
                )
            )
        seen_dates.add(bar.trade_date)

        if bar.open <= 0 or bar.high <= 0 or bar.low <= 0 or bar.close <= 0:
            issues.append(
                ValidationIssue(
                    check_name="non_positive_price",
                    message=f"Non-positive price on {bar.trade_date}",
                    security_id=security_id,  # type: ignore[arg-type]
                )
            )
        if bar.high < bar.low:
            issues.append(
                ValidationIssue(
                    check_name="invalid_ohlc",
                    message=f"high < low on {bar.trade_date}",
                    security_id=security_id,  # type: ignore[arg-type]
                )
            )
        if bar.high < max(bar.open, bar.close) or bar.low > min(bar.open, bar.close):
            issues.append(
                ValidationIssue(
                    check_name="invalid_ohlc",
                    message=f"OHLC inconsistent on {bar.trade_date}",
                    security_id=security_id,  # type: ignore[arg-type]
                )
            )

    return issues
