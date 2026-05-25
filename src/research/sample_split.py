"""Fixed chronological in-sample / out-of-sample split utilities."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import TypeVar

from core.enums import SamplePeriod
from core.types import SecurityId
from data.protocols import DataAccess
from research.config import SampleSplitMetadata
from schemas.backtest import EquityCurvePoint, Trade
from schemas.results import TradeRecord

TradeLike = TypeVar("TradeLike", Trade, TradeRecord)


@dataclass(frozen=True)
class SampleSplit:
    """Trading-day split boundaries for a research window."""

    calendar_start: date
    calendar_end: date
    is_fraction: Decimal
    split_date: date
    is_trading_days: int
    oos_trading_days: int
    trading_days: tuple[date, ...]

    @property
    def total_trading_days(self) -> int:
        return len(self.trading_days)


def last_completed_calendar_year_end(*, as_of: date | None = None) -> date:
    """Return December 31 of the most recently completed calendar year."""
    today = as_of or date.today()
    return date(today.year - 1, 12, 31)


def compute_sample_split(
    trading_days: Sequence[date],
    *,
    calendar_start: date,
    calendar_end: date,
    is_fraction: Decimal = Decimal("0.80"),
) -> SampleSplit:
    """Split sorted trading days into oldest IS fraction and most recent OOS."""
    if not trading_days:
        raise ValueError("At least one trading day is required to compute a sample split")
    if is_fraction <= Decimal("0") or is_fraction >= Decimal("1"):
        raise ValueError("is_fraction must be between 0 and 1")

    ordered = tuple(sorted(set(trading_days)))
    if ordered[0] < calendar_start or ordered[-1] > calendar_end:
        raise ValueError("Trading days must fall within the research calendar")

    total = len(ordered)
    is_count = int(Decimal(str(total)) * is_fraction)
    if is_count <= 0 or is_count >= total:
        raise ValueError(
            f"Cannot split {total} trading days with is_fraction={is_fraction}"
        )

    split_date = ordered[is_count]
    return SampleSplit(
        calendar_start=calendar_start,
        calendar_end=calendar_end,
        is_fraction=is_fraction,
        split_date=split_date,
        is_trading_days=is_count,
        oos_trading_days=total - is_count,
        trading_days=ordered,
    )


def classify_date(evaluation_date: date, split: SampleSplit) -> SamplePeriod:
    if evaluation_date < split.split_date:
        return SamplePeriod.IN_SAMPLE
    return SamplePeriod.OUT_OF_SAMPLE


def filter_trades_by_period(
    trades: Sequence[TradeLike],
    *,
    split: SampleSplit,
    sample_period: SamplePeriod,
) -> list[TradeLike]:
    """Assign closed trades to a sample period using exit_date."""
    filtered: list[TradeLike] = []
    for trade in trades:
        if trade.exit_date is None:
            continue
        period = classify_date(trade.exit_date, split)
        if period is sample_period:
            filtered.append(trade)
    return filtered


def filter_equity_curve(
    equity_curve: Sequence[EquityCurvePoint],
    *,
    split: SampleSplit,
    sample_period: SamplePeriod,
) -> list[EquityCurvePoint]:
    if sample_period is SamplePeriod.IN_SAMPLE:
        return [point for point in equity_curve if point.date < split.split_date]
    if sample_period is SamplePeriod.OUT_OF_SAMPLE:
        return [point for point in equity_curve if point.date >= split.split_date]
    return list(equity_curve)


def collect_trading_days(
    *sources: Iterable[date],
    calendar_start: date,
    calendar_end: date,
) -> list[date]:
    days = {
        day
        for source in sources
        for day in source
        if calendar_start <= day <= calendar_end
    }
    return sorted(days)


def collect_trading_days_from_data(
    data_access: DataAccess,
    security_ids: Sequence[SecurityId],
    *,
    calendar_start: date,
    calendar_end: date,
) -> list[date]:
    days: set[date] = set()
    for security_id in security_ids:
        bars = data_access.get_prices(
            security_id,
            calendar_start,
            calendar_end,
            calendar_end,
        )
        days.update(bar.trade_date for bar in bars)
    return sorted(days)


def split_to_metadata(split: SampleSplit) -> SampleSplitMetadata:
    return SampleSplitMetadata(
        is_fraction=split.is_fraction,
        calendar_start=split.calendar_start,
        calendar_end=split.calendar_end,
        split_date=split.split_date,
        is_trading_days=split.is_trading_days,
        oos_trading_days=split.oos_trading_days,
        total_trading_days=split.total_trading_days,
    )
