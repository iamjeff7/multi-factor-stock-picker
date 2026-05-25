"""Shared fixtures for reporting tests."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from core.enums import ExperimentStatus, ExperimentType
from core.types import (
    ConfigurationHash,
    DataVersion,
    ExperimentId,
    SecurityId,
    Ticker,
    TradeId,
    UniverseVersion,
)
from schemas.results import ExperimentMetadata, TradeRecord


@pytest.fixture
def sample_experiment_metadata() -> ExperimentMetadata:
    return ExperimentMetadata(
        experiment_id=ExperimentId("exp_test001"),
        experiment_name="Test Experiment",
        experiment_type=ExperimentType.SINGLE_FACTOR,
        execution_timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        data_version=DataVersion("data_001"),
        universe_version=UniverseVersion("universe_001"),
        configuration_hash=ConfigurationHash("abc123"),
        framework_version="2.0.0",
        status=ExperimentStatus.COMPLETED,
    )


@pytest.fixture
def sample_trade() -> TradeRecord:
    return TradeRecord(
        experiment_id=ExperimentId("exp_test001"),
        trade_id=TradeId("trade_001"),
        security_id=SecurityId("SEC_AAPL"),
        ticker=Ticker("AAPL"),
        entry_date=date(2020, 1, 2),
        entry_price=Decimal("100"),
        exit_date=date(2020, 1, 10),
        exit_price=Decimal("110"),
        shares=Decimal("10"),
        gross_pnl=Decimal("100"),
        net_pnl=Decimal("100"),
        holding_days=8,
        return_pct=Decimal("0.1"),
    )
