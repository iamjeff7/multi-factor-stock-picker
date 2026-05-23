"""Universe filter helpers."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from config.models import UniverseSettings
from core.enums import SecurityType
from schemas.data import DelistingInfo, PriceBar, SecurityMetadata


def is_delisted_on_or_before(
    delisting: DelistingInfo | None,
    evaluation_date: date,
) -> bool:
    if delisting is None:
        return False
    return delisting.delisting_date <= evaluation_date


def passes_exchange_filter(metadata: SecurityMetadata, settings: UniverseSettings) -> bool:
    allowed = {exchange.value for exchange in settings.allowed_exchanges}
    return metadata.exchange in allowed


def passes_security_type_filter(settings: UniverseSettings) -> bool:
    allowed = {security_type.value for security_type in settings.allowed_security_types}
    return SecurityType.COMMON_STOCK.value in allowed


def _bar_on_or_before(bars: list[PriceBar], trade_date: date) -> PriceBar | None:
    eligible = [bar for bar in bars if bar.trade_date <= trade_date]
    if not eligible:
        return None
    return max(eligible, key=lambda bar: bar.trade_date)


def passes_price_filter(
    bars: list[PriceBar],
    evaluation_date: date,
    min_price: float,
) -> bool:
    bar = _bar_on_or_before(bars, evaluation_date)
    if bar is None:
        return False
    return bar.close >= Decimal(str(min_price))


def passes_market_cap_filter(
    market_cap: Decimal | None,
    min_market_cap: float | None,
) -> bool:
    if min_market_cap is None:
        return True
    if market_cap is None:
        return False
    return market_cap >= Decimal(str(min_market_cap))