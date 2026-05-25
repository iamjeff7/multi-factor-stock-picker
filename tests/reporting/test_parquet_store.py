"""Parquet result store tests."""

from decimal import Decimal
from pathlib import Path

import pytest

from core.exceptions import ValidationError
from reporting.stores import ParquetResultStore, ValidatingResultStore
from schemas.results import (
    BacktestSummaryRecord,
    ConfigurationSnapshotRecord,
    ExperimentMetadata,
    TradeRecord,
    VersionMetadataRecord,
)


def test_parquet_store_round_trip(
    tmp_path: Path,
    sample_experiment_metadata: ExperimentMetadata,
    sample_trade: TradeRecord,
) -> None:
    store = ValidatingResultStore(ParquetResultStore(tmp_path))
    experiment_id = str(sample_experiment_metadata.experiment_id)
    store.create_experiment(sample_experiment_metadata)
    store.save_configuration_snapshot(
        ConfigurationSnapshotRecord(
            experiment_id=sample_experiment_metadata.experiment_id,
            configuration_hash=sample_experiment_metadata.configuration_hash,
            configuration_json={"initial_capital": 100000},
        )
    )
    store.save_version_metadata(
        VersionMetadataRecord(
            experiment_id=sample_experiment_metadata.experiment_id,
            framework_version="2.0.0",
            data_version=sample_experiment_metadata.data_version,
            universe_version=sample_experiment_metadata.universe_version,
            entry_signal_versions={"example_stub": "1.0"},
            exit_signal_versions={"example_stub_exit": "1.0"},
            backtest_version="2.0.0",
        )
    )
    store.save_trades([sample_trade])

    parquet_store = ParquetResultStore(tmp_path)
    loaded_metadata = parquet_store.load_experiment_metadata(experiment_id)
    loaded_trades = parquet_store.load_trades(experiment_id)

    assert loaded_metadata is not None
    assert loaded_metadata.experiment_id == sample_experiment_metadata.experiment_id
    assert len(loaded_trades) == 1
    assert loaded_trades[0].net_pnl == Decimal("100")


def test_parquet_store_rejects_overwrite(
    tmp_path: Path,
    sample_experiment_metadata: ExperimentMetadata,
) -> None:
    store = ParquetResultStore(tmp_path)
    store.create_experiment(sample_experiment_metadata)

    with pytest.raises(ValidationError, match="already exists"):
        store.create_experiment(sample_experiment_metadata)


def test_parquet_store_load_summary(
    tmp_path: Path,
    sample_experiment_metadata: ExperimentMetadata,
) -> None:
    store = ValidatingResultStore(ParquetResultStore(tmp_path))
    experiment_id = sample_experiment_metadata.experiment_id
    store.create_experiment(sample_experiment_metadata)
    store.save_backtest_summary(
        BacktestSummaryRecord(
            experiment_id=experiment_id,
            total_return=Decimal("0.12"),
            number_of_trades=6,
        )
    )

    loaded = ParquetResultStore(tmp_path).load_backtest_summary(str(experiment_id))
    assert loaded is not None
    assert loaded.total_return == Decimal("0.12")
    assert loaded.number_of_trades == 6
