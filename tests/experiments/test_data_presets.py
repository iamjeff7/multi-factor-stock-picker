"""Tests for data preset resolution."""

from datetime import date
from decimal import Decimal

import pytest

from core.exceptions import ValidationError
from core.types import DataVersion, SecurityId
from data.protocols import DataAccess
from experiments.data_presets import resolve_data_preset
from experiments.enums import DataPreset, DateResolution
from schemas.data import PriceBar


class _Mag7Access:
    data_version = DataVersion("mag7_test")

    def get_prices(
        self,
        security_id: SecurityId,
        start_date: date,
        end_date: date,
        as_of_date: date,
    ) -> list[PriceBar]:
        del security_id, as_of_date
        bars: list[PriceBar] = []
        for month in range(1, 13):
            trade_date = date(2025, month, 2)
            if start_date <= trade_date <= end_date:
                bars.append(
                    PriceBar(
                        trade_date=trade_date,
                        open=Decimal("100"),
                        high=Decimal("101"),
                        low=Decimal("99"),
                        close=Decimal("100"),
                        adjusted_close=Decimal("100"),
                        volume=1_000_000,
                    )
                )
        return bars


def test_demo_preset_uses_most_recent_complete_trading_year() -> None:
    access: DataAccess = _Mag7Access()
    preset = resolve_data_preset(
        DataPreset.DEMO,
        access,
        ["SEC_AAPL"],
        reference_date=date(2026, 5, 26),
    )
    assert preset.date_resolution is DateResolution.MOST_RECENT_COMPLETE_TRADING_YEAR
    assert preset.complete_calendar_year == 2025
    assert preset.start_date == date(2025, 1, 1)
    assert preset.end_date == date(2025, 12, 31)


def test_full_preset_is_unavailable() -> None:
    access: DataAccess = _Mag7Access()
    with pytest.raises(ValidationError, match="full is not available"):
        resolve_data_preset(DataPreset.FULL, access, ["SEC_AAPL"])
