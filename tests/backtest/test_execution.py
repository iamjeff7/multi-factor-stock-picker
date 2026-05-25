"""Execution model tests."""

from datetime import date
from decimal import Decimal

import pytest

from backtest.execution import NextBarExecutionModel
from core.enums import ExecutionPrice
from core.exceptions import ValidationError
from core.types import SecurityId


def test_execution_applies_buy_slippage(rising_price_access) -> None:
    execution = NextBarExecutionModel(
        execution_price=ExecutionPrice.NEXT_OPEN,
        slippage_pct=Decimal("0.001"),
        commission_pct=Decimal("0"),
    )
    fill = execution.get_fill_price(
        rising_price_access,
        SecurityId("SEC_TEST"),
        date(2020, 1, 3),
        is_buy=True,
    )
    assert fill.raw_price == Decimal("101")
    assert fill.fill_price == Decimal("101") * Decimal("1.001")


def test_execution_applies_sell_slippage(rising_price_access) -> None:
    execution = NextBarExecutionModel(
        execution_price=ExecutionPrice.NEXT_CLOSE,
        slippage_pct=Decimal("0.001"),
        commission_pct=Decimal("0"),
    )
    fill = execution.get_fill_price(
        rising_price_access,
        SecurityId("SEC_TEST"),
        date(2020, 1, 3),
        is_buy=False,
    )
    assert fill.fill_price == Decimal("101") * Decimal("0.999")


def test_execution_missing_bar_raises(rising_price_access) -> None:
    execution = NextBarExecutionModel(
        execution_price=ExecutionPrice.NEXT_OPEN,
        slippage_pct=Decimal("0"),
        commission_pct=Decimal("0"),
    )
    with pytest.raises(ValidationError, match="No price bar"):
        execution.get_fill_price(
            rising_price_access,
            SecurityId("SEC_TEST"),
            date(2020, 2, 1),
            is_buy=True,
        )
