"""Shared fixtures for backtest tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from core.types import DataVersion, SecurityId, Ticker
from data.protocols import DataAccess
from schemas.data import (
    CorporateAction,
    DelistingInfo,
    FundamentalRecord,
    PriceBar,
    SecurityMetadata,
)


class SyntheticDataAccess:
    """DataAccess backed by an in-memory price series."""

    def __init__(
        self,
        security_id: SecurityId,
        ticker: Ticker,
        prices: dict[date, Decimal],
        *,
        corporate_actions: list[CorporateAction] | None = None,
        delisting: DelistingInfo | None = None,
    ) -> None:
        self._security_id = security_id
        self._ticker = ticker
        self._prices = prices
        self._corporate_actions = corporate_actions or []
        self._delisting = delisting

    @property
    def data_version(self) -> DataVersion:
        return DataVersion("synthetic_001")

    def get_prices(
        self,
        security_id: SecurityId,
        start_date: date,
        end_date: date,
        as_of_date: date,
    ) -> list[PriceBar]:
        del security_id
        bars: list[PriceBar] = []
        for trade_date, close in sorted(self._prices.items()):
            if start_date <= trade_date <= end_date and trade_date <= as_of_date:
                bars.append(_bar(trade_date, close))
        return bars

    def get_fundamentals(
        self,
        security_id: SecurityId,
        as_of_date: date,
    ) -> list[FundamentalRecord]:
        del security_id, as_of_date
        return []

    def get_corporate_actions(
        self,
        security_id: SecurityId,
        as_of_date: date,
    ) -> list[CorporateAction]:
        del security_id
        return [
            action for action in self._corporate_actions if action.action_date <= as_of_date
        ]

    def get_metadata(
        self,
        security_id: SecurityId,
        as_of_date: date,
    ) -> SecurityMetadata | None:
        del as_of_date
        if security_id != self._security_id:
            return None
        return SecurityMetadata(
            security_id=self._security_id,
            ticker=self._ticker,
            permanent_security_id=str(self._security_id),
            company_name="Synthetic Co",
            exchange="NASDAQ",
            as_of_date=date(2020, 1, 1),
        )

    def get_delisting_info(
        self,
        security_id: SecurityId,
    ) -> DelistingInfo | None:
        del security_id
        return self._delisting

    def list_security_ids(self) -> list[SecurityId]:
        return [self._security_id]


def _bar(trade_date: date, close: Decimal) -> PriceBar:
    return PriceBar(
        trade_date=trade_date,
        open=close,
        high=close,
        low=close,
        close=close,
        adjusted_close=close,
        volume=1_000_000,
    )


@pytest.fixture
def synthetic_security() -> tuple[SecurityId, Ticker]:
    return SecurityId("SEC_TEST"), Ticker("TEST")


@pytest.fixture
def delisting_price_access(synthetic_security: tuple[SecurityId, Ticker]) -> DataAccess:
    security_id, ticker = synthetic_security
    prices = {
        date(2020, 1, 2): Decimal("100"),
        date(2020, 1, 3): Decimal("100"),
        date(2020, 1, 6): Decimal("100"),
        date(2020, 1, 7): Decimal("100"),
    }
    return SyntheticDataAccess(
        security_id,
        ticker,
        prices,
        delisting=DelistingInfo(
            security_id=security_id,
            delisting_date=date(2020, 1, 7),
            delisting_reason="acquired",
        ),
    )


@pytest.fixture
def rising_price_access(synthetic_security: tuple[SecurityId, Ticker]) -> DataAccess:
    security_id, ticker = synthetic_security
    prices = {
        date(2020, 1, 2): Decimal("100"),
        date(2020, 1, 3): Decimal("101"),
        date(2020, 1, 6): Decimal("102"),
        date(2020, 1, 7): Decimal("103"),
        date(2020, 1, 8): Decimal("104"),
        date(2020, 1, 9): Decimal("105"),
        date(2020, 1, 10): Decimal("106"),
        date(2020, 1, 13): Decimal("107"),
        date(2020, 1, 14): Decimal("108"),
        date(2020, 1, 15): Decimal("109"),
    }
    return SyntheticDataAccess(security_id, ticker, prices)
