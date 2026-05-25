"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import sys
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.types import (  # noqa: E402
    ConfigurationHash,
    DataVersion,
    PositionId,
    SecurityId,
    Ticker,
    UniverseVersion,
)
from data.protocols import DataAccess  # noqa: E402
from schemas.data import (  # noqa: E402
    CorporateAction,
    DelistingInfo,
    FundamentalRecord,
    PriceBar,
    SecurityMetadata,
)
from schemas.exit import PositionContext  # noqa: E402
from schemas.universe import (  # noqa: E402
    UniverseMembership,
    UniverseMembershipSnapshot,
    UniverseMetadata,
)


class MockDataAccess:
    """Minimal DataAccess stub for signal tests."""

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
        del security_id, start_date, end_date, as_of_date
        return []

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
        del security_id, as_of_date
        return []

    def get_metadata(
        self,
        security_id: SecurityId,
        as_of_date: date,
    ) -> SecurityMetadata | None:
        del security_id, as_of_date
        return None

    def get_delisting_info(
        self,
        security_id: SecurityId,
    ) -> DelistingInfo | None:
        del security_id
        return None

    def list_security_ids(self) -> list[SecurityId]:
        return []


@pytest.fixture
def mock_data_access() -> DataAccess:
    return MockDataAccess()


@pytest.fixture
def sample_universe_snapshot() -> UniverseMembershipSnapshot:
    evaluation_date = date(2020, 1, 31)
    return UniverseMembershipSnapshot(
        evaluation_date=evaluation_date,
        memberships=[
            UniverseMembership(
                evaluation_date=evaluation_date,
                security_id=SecurityId("100"),
                ticker=Ticker("AAA"),
                is_member=True,
            ),
            UniverseMembership(
                evaluation_date=evaluation_date,
                security_id=SecurityId("200"),
                ticker=Ticker("BBB"),
                is_member=True,
            ),
            UniverseMembership(
                evaluation_date=evaluation_date,
                security_id=SecurityId("300"),
                ticker=Ticker("CCC"),
                is_member=False,
            ),
        ],
        metadata=UniverseMetadata(
            universe_version=UniverseVersion("uni_001"),
            creation_timestamp=datetime(2020, 1, 31, tzinfo=UTC),
            configuration_hash=ConfigurationHash("abc123"),
            data_version=DataVersion("data_001"),
        ),
    )


@pytest.fixture
def sample_position() -> PositionContext:
    return PositionContext(
        position_id=PositionId("pos_001"),
        security_id=SecurityId("100"),
        ticker=Ticker("AAA"),
        entry_date=date(2020, 1, 2),
        entry_price=Decimal("100"),
        position_size=Decimal("10"),
        holding_period=100,
    )
