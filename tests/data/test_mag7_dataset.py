"""Mag7 dataset integration tests."""

from datetime import date

from config.models import UniverseSettings
from core.types import SecurityId
from data.universe.builder import DefaultUniverseBuilder
from data.validation import DatasetValidator


def test_mag7_dataset_validates(mag7_store) -> None:
    assert mag7_store is not None
    report = DatasetValidator().validate_all(mag7_store.dataset)
    assert report.passed is True


def test_mag7_members_include_all_tickers(mag7_store) -> None:
    assert mag7_store is not None
    builder = DefaultUniverseBuilder(UniverseSettings(minimum_trading_history_days=252))
    snapshot = builder.build_membership(date(2024, 6, 3), mag7_store)
    members = {m.security_id for m in snapshot.memberships if m.is_member}
    expected = {
        SecurityId("SEC_AAPL"),
        SecurityId("SEC_MSFT"),
        SecurityId("SEC_GOOGL"),
        SecurityId("SEC_AMZN"),
        SecurityId("SEC_META"),
        SecurityId("SEC_NVDA"),
        SecurityId("SEC_TSLA"),
    }
    assert expected.issubset(members)
