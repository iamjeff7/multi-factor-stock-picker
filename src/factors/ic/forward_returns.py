"""Forward return construction for IC analysis."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from backtest.calendar import next_trading_day
from core.types import SecurityId
from data.protocols import DataAccess
from entry_signals.validator import is_finite_decimal
from schemas.ic import ForwardReturn


class ForwardReturnCalculator:
    """Builds point-in-time forward returns from adjusted prices."""

    def calculate_for_universe(
        self,
        *,
        security_ids: Sequence[SecurityId],
        evaluation_date: date,
        horizon: int,
        trading_days: Sequence[date],
        data_access: DataAccess,
    ) -> list[ForwardReturn]:
        execution_date = next_trading_day(sorted(trading_days), evaluation_date)
        if execution_date is None:
            return []

        end_date = _forward_end_date(sorted(trading_days), execution_date, horizon)
        if end_date is None:
            return []

        returns: list[ForwardReturn] = []
        for security_id in security_ids:
            forward_return = self._calculate_security_return(
                security_id=security_id,
                evaluation_date=evaluation_date,
                execution_date=execution_date,
                end_date=end_date,
                horizon=horizon,
                data_access=data_access,
            )
            if forward_return is not None:
                returns.append(forward_return)
        return returns

    def _calculate_security_return(
        self,
        *,
        security_id: SecurityId,
        evaluation_date: date,
        execution_date: date,
        end_date: date,
        horizon: int,
        data_access: DataAccess,
    ) -> ForwardReturn | None:
        start_bar = _get_price_bar(
            data_access,
            security_id=security_id,
            trade_date=execution_date,
            as_of_date=end_date,
        )
        end_bar = _get_price_bar(
            data_access,
            security_id=security_id,
            trade_date=end_date,
            as_of_date=end_date,
        )
        if start_bar is None or end_bar is None:
            return None
        if start_bar.adjusted_close <= Decimal("0"):
            return None

        forward_return = (end_bar.adjusted_close / start_bar.adjusted_close) - Decimal("1")
        if not is_finite_decimal(forward_return):
            return None

        return ForwardReturn(
            evaluation_date=evaluation_date,
            security_id=security_id,
            horizon=horizon,
            forward_return=forward_return,
        )


def build_trading_calendar(
    data_access: DataAccess,
    security_ids: Sequence[SecurityId],
    *,
    start_date: date,
    end_date: date,
    as_of_date: date,
) -> list[date]:
    dates: set[date] = set()
    for security_id in security_ids:
        bars = data_access.get_prices(
            security_id=security_id,
            start_date=start_date,
            end_date=end_date,
            as_of_date=as_of_date,
        )
        dates.update(bar.trade_date for bar in bars)
    return sorted(dates)


def _forward_end_date(
    trading_days: list[date],
    execution_date: date,
    horizon: int,
) -> date | None:
    try:
        start_index = trading_days.index(execution_date)
    except ValueError:
        return None
    end_index = start_index + horizon
    if end_index >= len(trading_days):
        return None
    return trading_days[end_index]


def _get_price_bar(
    data_access: DataAccess,
    *,
    security_id: SecurityId,
    trade_date: date,
    as_of_date: date,
):
    bars = data_access.get_prices(
        security_id=security_id,
        start_date=trade_date,
        end_date=trade_date,
        as_of_date=as_of_date,
    )
    if not bars:
        return None
    return bars[0]
