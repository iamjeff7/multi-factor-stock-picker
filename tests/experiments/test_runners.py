"""Integration tests for unified experiment runners."""

from datetime import date
from pathlib import Path

import pytest

from config.loader import load_yaml_config
from data.loaders import ParquetLoader
from data.store import InMemoryDataStore
from experiments.config import UnifiedExperimentConfig
from experiments.entry_runner import EntryExperimentRunner
from experiments.exit_runner import ExitExperimentRunner


@pytest.fixture
def mag7_store() -> InMemoryDataStore:
    root = Path(__file__).resolve().parents[2]
    dataset = ParquetLoader().load(root / "tests" / "fixtures" / "data" / "mag7")
    return InMemoryDataStore(dataset)


def test_entry_demo_experiment_writes_report_and_rankings(
    mag7_store: InMemoryDataStore,
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    config = load_yaml_config(
        root / "configs" / "experiments" / "entry_demo.yaml",
        UnifiedExperimentConfig,
    )
    report_path = EntryExperimentRunner().run(
        config,
        mag7_store,
        output_dir=tmp_path,
        reference_date=date(2026, 5, 26),
    )
    assert report_path.exists()
    rankings_path = report_path.parent.parent / "rankings" / "entry_top_factors.json"
    assert rankings_path.exists()


def test_exit_demo_experiment_writes_report_and_rankings(
    mag7_store: InMemoryDataStore,
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    config = load_yaml_config(
        root / "configs" / "experiments" / "exit_demo.yaml",
        UnifiedExperimentConfig,
    )
    report_path = ExitExperimentRunner().run(
        config,
        mag7_store,
        output_dir=tmp_path,
        reference_date=date(2026, 5, 26),
    )
    assert report_path.exists()
    rankings_path = report_path.parent.parent / "rankings" / "exit_top_factors.json"
    assert rankings_path.exists()
