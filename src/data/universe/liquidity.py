"""Average daily dollar volume calculation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from schemas.data import PriceBar


def compute_addv(
    bars: list[PriceBar],
    evaluation_date: date,
    window_days: int = 60,
) -> Decimal | None:
    """Compute ADDV using only bars strictly before evaluation_date."""
    eligible = [bar for bar in bars if bar.trade_date < evaluation_date]
    if not eligible:
        return None

    eligible.sort(key=lambda bar: bar.trade_date)
    window = eligible[-window_days:]
    if not window:
        return None

    total = sum(Decimal(bar.volume) * bar.close for bar in window)
    return total / Decimal(len(window))


def count_trading_days_before(bars: list[PriceBar], evaluation_date: date) -> int:
    return sum(1 for bar in bars if bar.trade_date < evaluation_date)
