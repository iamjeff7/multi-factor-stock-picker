"""Shared price lookup helpers for exit signals."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from core.exceptions import MissingSignalDataError
from core.types import SecurityId
from data.protocols import DataAccess


def get_close_on_date(
    data_access: DataAccess,
    *,
    security_id: SecurityId,
    evaluation_date: date,
) -> Decimal:
    """Return the close on evaluation_date, or the last bar on or before it."""
    bars = data_access.get_prices(
        security_id=security_id,
        start_date=evaluation_date - timedelta(days=10),
        end_date=evaluation_date,
        as_of_date=evaluation_date,
    )
    eligible = [bar for bar in bars if bar.trade_date <= evaluation_date]
    if not eligible:
        raise MissingSignalDataError(
            f"No close price available for {security_id} on or before {evaluation_date}"
        )
    return eligible[-1].close
