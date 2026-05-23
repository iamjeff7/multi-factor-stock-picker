"""Parquet loader tests."""

from pathlib import Path

from core.types import SecurityId
from data.loaders import ParquetLoader

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "data" / "edge_cases"


def test_load_edge_case_dataset() -> None:
    dataset = ParquetLoader().load(FIXTURES)
    assert dataset.manifest.data_version == "edge_cases_001"
    assert SecurityId("SEC_NORMAL") in dataset.security_ids
