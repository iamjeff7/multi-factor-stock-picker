"""In-memory result store tests."""

import pytest

from core.exceptions import ValidationError
from reporting.stores import InMemoryResultStore, ValidatingResultStore
from schemas.results import ExperimentMetadata, TradeRecord


def test_memory_store_requires_experiment_before_save(sample_trade: TradeRecord) -> None:
    store = InMemoryResultStore()

    with pytest.raises(ValidationError, match="Experiment metadata must be created"):
        store.save_trades([sample_trade])


def test_validating_store_persists_trades(
    sample_experiment_metadata: ExperimentMetadata,
    sample_trade: TradeRecord,
) -> None:
    store = ValidatingResultStore(InMemoryResultStore())
    store.create_experiment(sample_experiment_metadata)
    store.save_trades([sample_trade])

    inner = store.inner
    assert isinstance(inner, InMemoryResultStore)
    assert len(inner.trades) == 1


def test_memory_store_rejects_duplicate_experiment(
    sample_experiment_metadata: ExperimentMetadata,
) -> None:
    store = InMemoryResultStore()
    store.create_experiment(sample_experiment_metadata)

    with pytest.raises(ValidationError, match="Experiment already exists"):
        store.create_experiment(sample_experiment_metadata)
