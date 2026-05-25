"""Tests for 6-1 momentum entry signal."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from backtest.experiment_config import SignalConfig
from backtest.signal_factory import build_entry_signal
from core.types import ConfigurationHash, DataVersion, SecurityId, Ticker, UniverseVersion
from data.loaders import ParquetLoader
from data.store import InMemoryDataStore
from entry_signals.enums import MissingDataPolicy
from entry_signals.momentum.momentum_6_1 import Momentum6_1EntrySignal
from schemas.data import PriceBar
from schemas.universe import (
    UniverseMembership,
    UniverseMembershipSnapshot,
    UniverseMetadata,
)


class SyntheticPriceDataAccess:
    def __init__(self, prices_by_security: dict[SecurityId, list[PriceBar]]) -> None:
        self._prices = prices_by_security

    @property
    def data_version(self) -> DataVersion:
        return DataVersion("test_data_001")

    def get_prices(
        self,
        security_id: SecurityId,
        start_date: date,
        end_date: date,
        as_of_date: date,
    ) -> list[PriceBar]:
        del as_of_date
        bars = self._prices.get(security_id, [])
        return [bar for bar in bars if start_date <= bar.trade_date <= end_date]

    def get_fundamentals(self, security_id: SecurityId, as_of_date: date):
        del security_id, as_of_date
        return []

    def get_corporate_actions(self, security_id: SecurityId, as_of_date: date):
        del security_id, as_of_date
        return []

    def get_metadata(self, security_id: SecurityId, as_of_date: date):
        del security_id, as_of_date
        return None

    def get_delisting_info(self, security_id: SecurityId):
        del security_id
        return None

    def list_security_ids(self) -> list[SecurityId]:
        return list(self._prices)


def _build_daily_prices(
    *,
    security_id: SecurityId,
    start_date: date,
    day_count: int,
    start_price: Decimal,
    daily_multiplier: Decimal,
) -> list[PriceBar]:
    bars: list[PriceBar] = []
    price = start_price
    for offset in range(day_count):
        trade_date = start_date + timedelta(days=offset)
        bars.append(
            PriceBar(
                trade_date=trade_date,
                open=price,
                high=price,
                low=price,
                close=price,
                adjusted_close=price,
                volume=1_000,
            )
        )
        price *= daily_multiplier
    return bars


def _membership_snapshot(
    evaluation_date: date,
    memberships: list[UniverseMembership],
) -> UniverseMembershipSnapshot:
    return UniverseMembershipSnapshot(
        evaluation_date=evaluation_date,
        memberships=memberships,
        metadata=UniverseMetadata(
            universe_version=UniverseVersion("uni_test"),
            creation_timestamp=datetime(2020, 1, 31, tzinfo=UTC),
            configuration_hash=ConfigurationHash("abc123"),
            data_version=DataVersion("data_test"),
        ),
    )


def test_momentum_6_1_computes_trailing_return_over_trading_days() -> None:
    security_id = SecurityId("SEC_TEST")
    start_date = date(2020, 1, 1)
    day_count = 200
    bars = _build_daily_prices(
        security_id=security_id,
        start_date=start_date,
        day_count=day_count,
        start_price=Decimal("100"),
        daily_multiplier=Decimal("1.001"),
    )
    data_access = SyntheticPriceDataAccess({security_id: bars})
    evaluation_date = start_date + timedelta(days=day_count - 1)
    snapshot = _membership_snapshot(
        evaluation_date,
        [
            UniverseMembership(
                evaluation_date=evaluation_date,
                security_id=security_id,
                ticker=Ticker("TEST"),
                is_member=True,
            )
        ],
    )

    signal = Momentum6_1EntrySignal(lookback_days=126, skip_days=21)
    results = signal.calculate(evaluation_date, snapshot, data_access)

    assert len(results) == 1
    end_index = (day_count - 1) - 21
    start_index = end_index - 126
    expected = (bars[end_index].adjusted_close / bars[start_index].adjusted_close) - Decimal("1")
    assert results[0].raw_signal_value == expected
    assert results[0].signal_id == "momentum_6_1"


def test_momentum_6_1_excludes_insufficient_history() -> None:
    security_id = SecurityId("SEC_SHORT")
    start_date = date(2024, 1, 1)
    bars = _build_daily_prices(
        security_id=security_id,
        start_date=start_date,
        day_count=100,
        start_price=Decimal("50"),
        daily_multiplier=Decimal("1"),
    )
    data_access = SyntheticPriceDataAccess({security_id: bars})
    evaluation_date = start_date + timedelta(days=99)
    snapshot = _membership_snapshot(
        evaluation_date,
        [
            UniverseMembership(
                evaluation_date=evaluation_date,
                security_id=security_id,
                ticker=Ticker("SHORT"),
                is_member=True,
            )
        ],
    )

    signal = Momentum6_1EntrySignal()
    results = signal.calculate(evaluation_date, snapshot, data_access)

    assert results == []


def test_signal_factory_builds_momentum_6_1() -> None:
    signal = build_entry_signal(
        SignalConfig(
            name="momentum_6_1",
            params={"lookback_days": 63, "skip_days": 10},
        )
    )

    assert isinstance(signal, Momentum6_1EntrySignal)
    assert signal.lookback_days == 63
    assert signal.skip_days == 10
    assert signal.missing_data_policy is MissingDataPolicy.EXCLUDE_SECURITY


def test_momentum_6_1_on_mag7_fixture() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "data" / "mag7"
    if not fixture_dir.exists():
        pytest.skip("Mag7 fixture unavailable")

    mag7_store = InMemoryDataStore(ParquetLoader().load(fixture_dir))
    evaluation_date = date(2024, 6, 3)
    memberships = [
        UniverseMembership(
            evaluation_date=evaluation_date,
            security_id=security_id,
            ticker=Ticker(str(security_id).removeprefix("SEC_")),
            is_member=True,
        )
        for security_id in (
            SecurityId("SEC_AAPL"),
            SecurityId("SEC_MSFT"),
            SecurityId("SEC_NVDA"),
        )
    ]
    snapshot = _membership_snapshot(evaluation_date, memberships)
    signal = Momentum6_1EntrySignal()
    results = signal.calculate(evaluation_date, snapshot, mag7_store)

    assert len(results) == 3
    assert all(result.raw_signal_value is not None for result in results)
    assert all(result.signal_id == "momentum_6_1" for result in results)
