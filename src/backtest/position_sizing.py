"""Position sizing for single-stock backtests."""

from __future__ import annotations

from decimal import ROUND_FLOOR, Decimal
from typing import Protocol

from backtest.execution import ExecutionFill
from core.enums import PositionSizeMethod
from core.exceptions import ValidationError


class PositionSizer(Protocol):
    """Determines share count for an entry order."""

    def size_entry(
        self,
        available_cash: Decimal,
        fill: ExecutionFill,
        commission: Decimal,
    ) -> Decimal: ...


class FixedDollarSizer:
    """Allocate a fixed dollar amount per entry."""

    def __init__(self, dollar_amount: Decimal) -> None:
        if dollar_amount <= Decimal("0"):
            raise ValidationError("fixed_dollar_amount must be positive")
        self._dollar_amount = dollar_amount

    def size_entry(
        self,
        available_cash: Decimal,
        fill: ExecutionFill,
        commission: Decimal,
    ) -> Decimal:
        del commission
        budget = min(self._dollar_amount, available_cash)
        if fill.fill_price <= Decimal("0"):
            raise ValidationError("Fill price must be positive for sizing")
        shares = (budget / fill.fill_price).to_integral_value(rounding=ROUND_FLOOR)
        if shares <= Decimal("0"):
            raise ValidationError("Insufficient capital for entry")
        return shares


class FullCapitalSizer:
    """Deploy all available cash into the single position."""

    def size_entry(
        self,
        available_cash: Decimal,
        fill: ExecutionFill,
        commission: Decimal,
    ) -> Decimal:
        if fill.fill_price <= Decimal("0"):
            raise ValidationError("Fill price must be positive for sizing")
        deployable = available_cash - commission
        if deployable <= Decimal("0"):
            raise ValidationError("Insufficient capital for entry")
        shares = (deployable / fill.fill_price).to_integral_value(rounding=ROUND_FLOOR)
        if shares <= Decimal("0"):
            raise ValidationError("Insufficient capital for entry")
        return shares


def build_position_sizer(
    method: PositionSizeMethod,
    fixed_dollar_amount: Decimal | None,
) -> PositionSizer:
    if method is PositionSizeMethod.FIXED_DOLLAR:
        if fixed_dollar_amount is None:
            raise ValidationError("fixed_dollar_amount is required for FIXED_DOLLAR sizing")
        return FixedDollarSizer(fixed_dollar_amount)
    if method is PositionSizeMethod.EQUAL_WEIGHT:
        return FullCapitalSizer()
    raise ValidationError(f"Unsupported position sizing method for single-stock mode: {method}")
