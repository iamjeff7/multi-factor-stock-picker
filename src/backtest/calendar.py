"""Trading calendar utilities."""

from __future__ import annotations

from datetime import date

from core.enums import RebalanceFrequency


def trading_days_between(price_dates: list[date], start_date: date, end_date: date) -> list[date]:
    return sorted(day for day in price_dates if start_date <= day <= end_date)


def next_trading_day(trading_days: list[date], current_date: date) -> date | None:
    for day in trading_days:
        if day > current_date:
            return day
    return None


def is_rebalance_date(
    current_date: date,
    previous_date: date | None,
    frequency: RebalanceFrequency,
) -> bool:
    if frequency is RebalanceFrequency.DAILY:
        return True
    if previous_date is None:
        return True
    if frequency is RebalanceFrequency.WEEKLY:
        return current_date.isocalendar()[:2] != previous_date.isocalendar()[:2]
    if frequency is RebalanceFrequency.MONTHLY:
        return (current_date.year, current_date.month) != (previous_date.year, previous_date.month)
    if frequency is RebalanceFrequency.QUARTERLY:
        current_quarter = (current_date.year, (current_date.month - 1) // 3)
        previous_quarter = (previous_date.year, (previous_date.month - 1) // 3)
        return current_quarter != previous_quarter
    return False
