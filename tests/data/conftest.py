"""Shared fixtures for data layer tests."""

from pathlib import Path

import pytest

from data.loaders import ParquetLoader
from data.store import InMemoryDataStore

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "data"


@pytest.fixture
def edge_case_store() -> InMemoryDataStore:
    dataset = ParquetLoader().load(FIXTURES_DIR / "edge_cases")
    return InMemoryDataStore(dataset)


@pytest.fixture
def mag7_store() -> InMemoryDataStore | None:
    mag7_path = FIXTURES_DIR / "mag7"
    if not mag7_path.exists():
        return None
    dataset = ParquetLoader().load(mag7_path)
    return InMemoryDataStore(dataset)
