"""Single-factor experiment runner tests."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from backtest.experiment_config import (
    ExperimentSecurity,
    SignalConfig,
    SingleFactorExperimentConfig,
)
from backtest.experiment_runner import SingleFactorExperimentRunner
from core.enums import (
    PortfolioMode,
    PositionSizeMethod,
    RebalanceFrequency,
    ResearchMode,
    ResearchPhase,
    SamplePeriod,
    SampleScope,
)
from core.types import SecurityId, Ticker
from entry_signals.examples.stub_entry_signal import ExampleStubEntrySignal
from exit_signals.examples.stub_exit_signal import ExampleStubExitSignal
from reporting.stores import ParquetResultStore
from research.config import ResearchSettings


def test_experiment_runner_resets_capital_per_stock(rising_price_access, tmp_path: Path) -> None:
    config = SingleFactorExperimentConfig(
        experiment_name="two_stock_experiment",
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 10),
        initial_capital=10_000,
        rebalance_frequency=RebalanceFrequency.DAILY,
        portfolio_mode=PortfolioMode.SINGLE,
        position_size_method=PositionSizeMethod.FIXED_DOLLAR,
        fixed_dollar_amount=Decimal("1000"),
        securities=[
            ExperimentSecurity(security_id=SecurityId("SEC_TEST"), ticker=Ticker("TEST")),
            ExperimentSecurity(security_id=SecurityId("SEC_MISSING"), ticker=Ticker("MISSING")),
        ],
        entry_signal=SignalConfig(name="example_stub"),
        exit_signal=SignalConfig(name="example_stub_exit", params={"max_holding_days": 3}),
        research=ResearchSettings(
            research_mode=ResearchMode.TEST,
            research_phase=ResearchPhase.VALIDATION,
            sample_scope=SampleScope.FULL,
        ),
    )

    result = SingleFactorExperimentRunner().run(
        config=config,
        data_access=rising_price_access,
        entry_signal=ExampleStubEntrySignal(),
        exit_signal=ExampleStubExitSignal(max_holding_days=3),
        output_dir=tmp_path,
    )

    assert result.securities_completed == 2
    assert result.securities_skipped == 0
    assert len(result.stock_summaries) == 2
    assert result.experiment_summary.number_of_trades > 0
    assert result.experiment_summary.securities_requested == 2
    assert len(result.sample_summaries) == 2
    assert {summary.sample_period for summary in result.sample_summaries} == {
        SamplePeriod.IN_SAMPLE,
        SamplePeriod.OUT_OF_SAMPLE,
    }
    assert result.sample_split is not None
    assert result.degradation is not None

    parquet_store = ParquetResultStore(tmp_path)
    experiment_id = str(result.experiment_id)
    assert parquet_store.load_experiment_metadata(experiment_id) is not None
    summaries = parquet_store.load_experiment_summaries(experiment_id)
    assert len(summaries) == 3
    assert (tmp_path / experiment_id / "reports" / "experiment_report.json").exists()


def test_experiment_config_rejects_empty_securities_without_universe() -> None:
    with pytest.raises(ValueError, match="Provide securities or universe settings"):
        SingleFactorExperimentConfig(
            experiment_name="missing_universe",
            start_date=date(2020, 1, 2),
            end_date=date(2020, 1, 8),
            portfolio_mode=PortfolioMode.SINGLE,
            entry_signal=SignalConfig(name="example_stub"),
            exit_signal=SignalConfig(name="example_stub_exit"),
            research=ResearchSettings(
                research_mode=ResearchMode.TEST,
                research_phase=ResearchPhase.VALIDATION,
                sample_scope=SampleScope.FULL,
            ),
        )


def test_experiment_config_rejects_discovery_with_full_scope() -> None:
    with pytest.raises(ValueError, match="DISCOVERY phase requires sample_scope=IS"):
        SingleFactorExperimentConfig(
            experiment_name="invalid_discovery",
            start_date=date(2020, 1, 2),
            end_date=date(2020, 1, 8),
            initial_capital=10_000,
            rebalance_frequency=RebalanceFrequency.DAILY,
            portfolio_mode=PortfolioMode.SINGLE,
            position_size_method=PositionSizeMethod.FIXED_DOLLAR,
            fixed_dollar_amount=Decimal("1000"),
            securities=[
                ExperimentSecurity(security_id=SecurityId("SEC_TEST"), ticker=Ticker("TEST")),
            ],
            entry_signal=SignalConfig(name="example_stub"),
            exit_signal=SignalConfig(name="example_stub_exit", params={"max_holding_days": 3}),
            research=ResearchSettings(
                research_phase=ResearchPhase.DISCOVERY,
                sample_scope=SampleScope.FULL,
            ),
        )
