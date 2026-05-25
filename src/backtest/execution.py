"""Trade execution models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from core.enums import ExecutionPrice
from core.exceptions import ValidationError
from core.types import SecurityId
from data.protocols import DataAccess
from schemas.data import PriceBar


@dataclass(frozen=True)
class ExecutionFill:
    execution_date: date
    raw_price: Decimal
    fill_price: Decimal
    commission: Decimal


class NextBarExecutionModel:
    """Executes orders on a later bar using a configurable price field."""

    def __init__(
        self,
        execution_price: ExecutionPrice,
        slippage_pct: Decimal,
        commission_pct: Decimal,
        commission_per_trade: Decimal | None = None,
    ) -> None:
        self._execution_price = execution_price
        self._slippage_pct = slippage_pct
        self._commission_pct = commission_pct
        self._commission_per_trade = commission_per_trade

    @property
    def execution_price(self) -> ExecutionPrice:
        return self._execution_price

    def get_fill_price(
        self,
        data_access: DataAccess,
        security_id: SecurityId,
        execution_date: date,
        *,
        is_buy: bool,
    ) -> ExecutionFill:
        bar = self._get_bar(data_access, security_id, execution_date)
        raw_price = self._select_price(bar)
        if is_buy:
            fill_price = raw_price * (Decimal("1") + self._slippage_pct)
        else:
            fill_price = raw_price * (Decimal("1") - self._slippage_pct)
        return ExecutionFill(
            execution_date=execution_date,
            raw_price=raw_price,
            fill_price=fill_price,
            commission=Decimal("0"),
        )

    def calculate_commission(self, notional: Decimal) -> Decimal:
        commission = notional * self._commission_pct
        if self._commission_per_trade is not None:
            commission += self._commission_per_trade
        return commission

    def _get_bar(
        self,
        data_access: DataAccess,
        security_id: SecurityId,
        execution_date: date,
    ) -> PriceBar:
        bars = data_access.get_prices(
            security_id=security_id,
            start_date=execution_date,
            end_date=execution_date,
            as_of_date=execution_date,
        )
        if not bars:
            raise ValidationError(
                f"No price bar available for {security_id} on execution date {execution_date}"
            )
        return bars[0]

    def _select_price(self, bar: PriceBar) -> Decimal:
        if self._execution_price is ExecutionPrice.NEXT_OPEN:
            return bar.open
        if self._execution_price is ExecutionPrice.NEXT_CLOSE:
            return bar.close
        if bar.vwap is not None:
            return bar.vwap
        return (bar.high + bar.low + bar.close) / Decimal("3")
