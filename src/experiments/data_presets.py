"""Resolve experiment date ranges and universes from data presets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from core.exceptions import ValidationError
from data.protocols import DataAccess
from experiments.enums import DataPreset, DateResolution
from research.sample_split import collect_trading_days_from_data


@dataclass(frozen=True)
class ResolvedDataPreset:
    data_preset: DataPreset
    date_resolution: DateResolution
    start_date: date
    end_date: date
    trading_days: int
    complete_calendar_year: int | None = None
    universe_name: str = "mag7"


def resolve_data_preset(
    preset: DataPreset,
    data_access: DataAccess,
    security_ids: list[str],
    *,
    reference_date: date | None = None,
) -> ResolvedDataPreset:
    ref = reference_date or date.today()

    if preset is DataPreset.DEMO:
        complete_year = ref.year - 1
        start = date(complete_year, 1, 1)
        end = date(complete_year, 12, 31)
        trading_days = _count_trading_days(data_access, security_ids, start, end)
        return ResolvedDataPreset(
            data_preset=preset,
            date_resolution=DateResolution.MOST_RECENT_COMPLETE_TRADING_YEAR,
            start_date=start,
            end_date=end,
            trading_days=trading_days,
            complete_calendar_year=complete_year,
            universe_name="mag7",
        )

    if preset is DataPreset.EXTENDED_DEMO:
        start = date(2005, 1, 1)
        end = date(2025, 12, 31)
        trading_days = _count_trading_days(data_access, security_ids, start, end)
        return ResolvedDataPreset(
            data_preset=preset,
            date_resolution=DateResolution.FIXED_RANGE,
            start_date=start,
            end_date=end,
            trading_days=trading_days,
            universe_name="mag7",
        )

    if preset is DataPreset.FULL:
        raise ValidationError(
            "data_preset=full is not available yet; use demo or extended_demo"
        )

    raise ValidationError(f"Unknown data preset: {preset}")


def _count_trading_days(
    data_access: DataAccess,
    security_ids: list[str],
    start: date,
    end: date,
) -> int:
    from core.types import SecurityId

    ids = [SecurityId(value) for value in security_ids]
    days = collect_trading_days_from_data(
        data_access,
        ids,
        calendar_start=start,
        calendar_end=end,
    )
    return len(days)
