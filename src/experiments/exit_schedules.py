"""Resolve exit dates for entry factor evaluation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from backtest.calendar import next_trading_day
from schemas.data import PriceBar

def fixed_period_exit_date(
    entry_date: date,
    trading_days: list[date],
    *,
    holding_months: int,
) -> date | None:
    target = _add_calendar_months(entry_date, holding_months)
    for day in trading_days:
        if day >= target:
            return day
    return trading_days[-1] if trading_days else None


def _add_calendar_months(start: date, months: int) -> date:
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, _days_in_month(year, month))
    return date(year, month, day)


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    first = date(year, month, 1)
    return (next_month - first).days


def best_within_period_exit_date(
    entry_date: date,
    trading_days: list[date],
    closes: dict[date, Decimal],
    *,
    forward_trading_days: int,
) -> date | None:
    if entry_date not in closes:
        return None
    entry_price = closes[entry_date]
    if entry_price <= Decimal("0"):
        return None

    future_days = [day for day in trading_days if day > entry_date][:forward_trading_days]
    if not future_days:
        return None

    best_day = future_days[0]
    best_return = Decimal("-1")
    for day in future_days:
        close = closes.get(day)
        if close is None or close <= Decimal("0"):
            continue
        trade_return = (close / entry_price) - Decimal("1")
        if trade_return > best_return:
            best_return = trade_return
            best_day = day
    return best_day


def build_close_lookup(bars: list[PriceBar]) -> dict[date, Decimal]:
    return {bar.trade_date: bar.adjusted_close for bar in bars}


def entry_execution_day(entry_signal_day: date, trading_days: list[date]) -> date | None:
    return next_trading_day(trading_days, entry_signal_day) or entry_signal_day
