"""Universe builder tests."""

from datetime import date

from config.models import UniverseSettings
from core.types import SecurityId
from data.store import InMemoryDataStore
from data.universe.builder import DefaultUniverseBuilder


def _member(snapshot, security_id: str):
    return next(m for m in snapshot.memberships if m.security_id == SecurityId(security_id))


def test_universe_edge_cases(edge_case_store: InMemoryDataStore) -> None:
    eval_date = date(2023, 12, 29)
    builder = DefaultUniverseBuilder(UniverseSettings(minimum_trading_history_days=252))
    snapshot = builder.build_membership(eval_date, edge_case_store)

    assert _member(snapshot, "SEC_NORMAL").is_member is True
    assert _member(snapshot, "SEC_ILLIQ").is_member is False
    assert _member(snapshot, "SEC_ILLIQ").membership_reason == "below_min_addv"
    assert _member(snapshot, "SEC_DELIST").is_member is False
    assert _member(snapshot, "SEC_DELIST").membership_reason == "delisted"


def test_ipo_insufficient_history(edge_case_store: InMemoryDataStore) -> None:
    eval_date = date(2024, 3, 1)
    builder = DefaultUniverseBuilder(UniverseSettings(minimum_trading_history_days=252))
    snapshot = builder.build_membership(eval_date, edge_case_store)
    ipo = _member(snapshot, "SEC_IPO")
    assert ipo.is_member is False
    assert ipo.membership_reason == "insufficient_trading_history"


def test_optional_market_cap_skipped_when_null(edge_case_store: InMemoryDataStore) -> None:
    settings = UniverseSettings(min_market_cap=None)
    builder = DefaultUniverseBuilder(settings)
    snapshot = builder.build_membership(date(2023, 12, 29), edge_case_store)
    normal = _member(snapshot, "SEC_NORMAL")
    assert normal.is_member is True
