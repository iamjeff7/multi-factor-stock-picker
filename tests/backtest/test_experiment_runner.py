"""Single-factor experiment runner tests."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from backtest.experiment_config import (
    ExperimentSecurity,
    SignalConfig,
    SingleFactorExperimentConfig,
)
from backtest.experiment_runner import SingleFactorExperimentRunner
from core.enums import PortfolioMode, PositionSizeMethod, RebalanceFrequency
from core.types import SecurityId, Ticker
from entry_signals.examples.stub_entry_signal import ExampleStubEntrySignal
from exit_signals.examples.stub_exit_signal import ExampleStubExitSignal
from reporting.stores import ParquetResultStore


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

    parquet_store = ParquetResultStore(tmp_path)
    experiment_id = str(result.experiment_id)
    assert parquet_store.load_experiment_metadata(experiment_id) is not None
    assert parquet_store.load_experiment_summary(experiment_id) is not None
    assert (tmp_path / experiment_id / "reports" / "experiment_report.json").exists()
