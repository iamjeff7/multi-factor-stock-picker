"""Point-in-time access tests."""

from datetime import date
from decimal import Decimal

from core.types import SecurityId
from data.store import InMemoryDataStore


def test_future_bars_not_visible(edge_case_store: InMemoryDataStore) -> None:
    as_of = date(2023, 1, 15)
    bars = edge_case_store.get_prices(
        SecurityId("SEC_NORMAL"),
        start_date=date(2023, 1, 1),
        end_date=as_of,
        as_of_date=as_of,
    )
    assert bars
    assert all(bar.trade_date <= as_of for bar in bars)
    assert max(bar.trade_date for bar in bars) <= as_of


def test_end_date_after_as_of_raises(edge_case_store: InMemoryDataStore) -> None:
    try:
        edge_case_store.get_prices(
            SecurityId("SEC_NORMAL"),
            start_date=date(2023, 1, 1),
            end_date=date(2023, 2, 1),
            as_of_date=date(2023, 1, 1),
        )
    except Exception as exc:
        assert "exceeds as_of_date" in str(exc)
    else:
        raise AssertionError("Expected ValidationError")


def test_fundamentals_respect_availability_date() -> None:
    from datetime import UTC, datetime

    from data.loaders.dataset import LoadedDataset
    from data.loaders.manifest import DatasetManifest
    from schemas.data import FundamentalRecord

    manifest = DatasetManifest(
        data_version="test",
        creation_timestamp=datetime.now(tz=UTC),
    )
    dataset = LoadedDataset(manifest=manifest)
    sid = SecurityId("SEC_TEST")
    dataset.fundamentals[sid] = [
        FundamentalRecord(
            security_id=sid,
            metric_name="revenue",
            reporting_period_end=date(2023, 3, 31),
            filing_date=date(2023, 4, 15),
            availability_date=date(2023, 4, 20),
            value=Decimal("100"),
        )
    ]
    store = InMemoryDataStore(dataset)
    assert not store.get_fundamentals(sid, date(2023, 4, 19))
    assert store.get_fundamentals(sid, date(2023, 4, 20))
