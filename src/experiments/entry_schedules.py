"""Generate synthetic entry schedules for exit experiments."""

from __future__ import annotations

from datetime import date, timedelta

from backtest.calendar import is_rebalance_date
from core.enums import RebalanceFrequency
from core.types import SecurityId
from data.protocols import DataAccess
from experiments.enums import EntryCadence
from schemas.data import PriceBar


def collect_scheduled_entry_dates(
    trading_days: list[date],
    cadence: EntryCadence,
) -> list[date]:
    frequency = _cadence_to_frequency(cadence)
    entries: list[date] = []
    previous: date | None = None
    for current in trading_days:
        if is_rebalance_date(current, previous, frequency):
            entries.append(current)
        previous = current
    return entries


def collect_bottom_entry_dates(
    bars: list[PriceBar],
    trading_days: list[date],
) -> list[date]:
    """Detect lower-low then higher-low on close; look-ahead allowed."""
    closes = {bar.trade_date: bar.close for bar in bars}
    entries: list[date] = []
    eligible_days = [day for day in trading_days if day in closes]
    if len(eligible_days) < 5:
        return entries

    swing_lows: list[tuple[date, float]] = []
    for index in range(2, len(eligible_days) - 2):
        day = eligible_days[index]
        prev_day = eligible_days[index - 1]
        next_day = eligible_days[index + 1]
        close = float(closes[day])
        if close <= float(closes[prev_day]) and close <= float(closes[next_day]):
            swing_lows.append((day, close))

    for index in range(2, len(swing_lows)):
        _, low1 = swing_lows[index - 2]
        day2, low2 = swing_lows[index - 1]
        day3, low3 = swing_lows[index]
        if low2 < low1 and low3 > low2:
            entries.append(day3)
    return entries


def load_price_bars(
    data_access: DataAccess,
    security_id: SecurityId,
    start_date: date,
    end_date: date,
) -> list[PriceBar]:
    return data_access.get_prices(
        security_id=security_id,
        start_date=start_date - timedelta(days=30),
        end_date=end_date,
        as_of_date=end_date,
    )


def _cadence_to_frequency(cadence: EntryCadence) -> RebalanceFrequency:
    if cadence is EntryCadence.DAY:
        return RebalanceFrequency.DAILY
    if cadence is EntryCadence.WEEK:
        return RebalanceFrequency.WEEKLY
    if cadence is EntryCadence.TWO_WEEKS:
        return RebalanceFrequency.WEEKLY
    return RebalanceFrequency.MONTHLY
