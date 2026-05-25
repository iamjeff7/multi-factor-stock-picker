"""Single-stock backtest engine tests."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from backtest.config import SingleStockBacktestConfig
from backtest.engine import SingleStockBacktestEngine
from backtest.entry_policy import SignalPresentEntryPolicy
from backtest.result_store import InMemoryResultStore
from core.enums import ExecutionPrice, PortfolioMode, PositionSizeMethod, RebalanceFrequency
from core.types import SecurityId, Ticker
from entry_signals.examples.stub_entry_signal import ExampleStubEntrySignal
from exit_signals.examples.stub_exit_signal import ExampleStubExitSignal
from reporting.stores import ParquetResultStore, ValidatingResultStore


def test_engine_runs_entry_exit_lifecycle(rising_price_access) -> None:
    config = SingleStockBacktestConfig(
        security_id=SecurityId("SEC_TEST"),
        ticker=Ticker("TEST"),
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 15),
        initial_capital=10_000,
        execution_price=ExecutionPrice.NEXT_OPEN,
        slippage_pct=0.0,
        commission_pct=0.0,
        rebalance_frequency=RebalanceFrequency.DAILY,
        portfolio_mode=PortfolioMode.SINGLE,
        position_size_method=PositionSizeMethod.EQUAL_WEIGHT,
    )
    engine = SingleStockBacktestEngine()
    result = engine.run(
        config=config,
        data_access=rising_price_access,
        entry_signal=ExampleStubEntrySignal(),
        exit_signal=ExampleStubExitSignal(max_holding_days=5),
        entry_policy=SignalPresentEntryPolicy(),
    )

    closed = [trade for trade in result.trades if trade.exit_date is not None]
    assert len(closed) >= 1
    assert result.final_portfolio_value > Decimal("0")
    assert len(result.equity_curve) == len(result.snapshots)


def test_engine_persists_results(rising_price_access) -> None:
    config = SingleStockBacktestConfig(
        security_id=SecurityId("SEC_TEST"),
        ticker=Ticker("TEST"),
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 10),
        initial_capital=10_000,
        rebalance_frequency=RebalanceFrequency.DAILY,
        portfolio_mode=PortfolioMode.SINGLE,
        position_size_method=PositionSizeMethod.FIXED_DOLLAR,
        fixed_dollar_amount=Decimal("1000"),
    )
    store = InMemoryResultStore()
    engine = SingleStockBacktestEngine()
    engine.run(
        config=config,
        data_access=rising_price_access,
        entry_signal=ExampleStubEntrySignal(),
        exit_signal=ExampleStubExitSignal(max_holding_days=3),
        result_store=store,
    )

    assert store.experiment is not None
    assert store.summary is not None
    assert store.configuration_snapshot is not None
    assert store.version_metadata is not None
    assert store.report_manifest is not None
    assert len(store.stock_summaries) == 1
    assert len(store.equity_curve) > 0


def test_engine_forces_delisting_exit(delisting_price_access) -> None:
    config = SingleStockBacktestConfig(
        security_id=SecurityId("SEC_TEST"),
        ticker=Ticker("TEST"),
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 7),
        initial_capital=10_000,
        rebalance_frequency=RebalanceFrequency.DAILY,
        portfolio_mode=PortfolioMode.SINGLE,
        position_size_method=PositionSizeMethod.FIXED_DOLLAR,
        fixed_dollar_amount=Decimal("1000"),
    )
    engine = SingleStockBacktestEngine()
    result = engine.run(
        config=config,
        data_access=delisting_price_access,
        entry_signal=ExampleStubEntrySignal(),
        exit_signal=ExampleStubExitSignal(max_holding_days=100),
    )
    closed = [trade for trade in result.trades if trade.exit_date is not None]
    assert len(closed) == 1
    assert closed[0].exit_date is not None


def test_engine_persists_to_parquet(tmp_path: Path, rising_price_access) -> None:
    config = SingleStockBacktestConfig(
        security_id=SecurityId("SEC_TEST"),
        ticker=Ticker("TEST"),
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 10),
        initial_capital=10_000,
        rebalance_frequency=RebalanceFrequency.DAILY,
        portfolio_mode=PortfolioMode.SINGLE,
        position_size_method=PositionSizeMethod.FIXED_DOLLAR,
        fixed_dollar_amount=Decimal("1000"),
    )
    store = ValidatingResultStore(ParquetResultStore(tmp_path))
    engine = SingleStockBacktestEngine()
    result = engine.run(
        config=config,
        data_access=rising_price_access,
        entry_signal=ExampleStubEntrySignal(),
        exit_signal=ExampleStubExitSignal(max_holding_days=3),
        result_store=store,
    )

    parquet_store = ParquetResultStore(tmp_path)
    experiment_id = str(result.experiment_id)
    assert parquet_store.load_experiment_metadata(experiment_id) is not None
    assert parquet_store.load_trades(experiment_id)
    assert parquet_store.load_stock_summaries(experiment_id)
    assert parquet_store.load_backtest_summary(experiment_id) is not None
    assert parquet_store.load_report_manifest(experiment_id) is not None
