"""Position sizing tests."""

from datetime import date
from decimal import Decimal

import pytest

from backtest.execution import ExecutionFill
from backtest.position_sizing import FixedDollarSizer, FullCapitalSizer
from core.exceptions import ValidationError


def test_fixed_dollar_sizer() -> None:
    sizer = FixedDollarSizer(Decimal("1000"))
    fill = ExecutionFill(
        execution_date=date(2020, 1, 3),
        raw_price=Decimal("100"),
        fill_price=Decimal("100"),
        commission=Decimal("0"),
    )
    shares = sizer.size_entry(Decimal("50000"), fill, Decimal("0"))
    assert shares == Decimal("10")


def test_full_capital_sizer() -> None:
    sizer = FullCapitalSizer()
    fill = ExecutionFill(
        execution_date=date(2020, 1, 3),
        raw_price=Decimal("100"),
        fill_price=Decimal("100"),
        commission=Decimal("0"),
    )
    shares = sizer.size_entry(Decimal("10000"), fill, Decimal("0"))
    assert shares == Decimal("100")


def test_full_capital_sizer_rejects_insufficient_cash() -> None:
    sizer = FullCapitalSizer()
    fill = ExecutionFill(
        execution_date=date(2020, 1, 3),
        raw_price=Decimal("100"),
        fill_price=Decimal("100"),
        commission=Decimal("0"),
    )
    with pytest.raises(ValidationError, match="Insufficient capital"):
        sizer.size_entry(Decimal("50"), fill, Decimal("0"))
