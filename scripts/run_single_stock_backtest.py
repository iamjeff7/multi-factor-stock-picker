#!/usr/bin/env python3
"""Example single-stock backtest run."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from backtest.config import SingleStockBacktestConfig  # noqa: E402
from backtest.engine import SingleStockBacktestEngine  # noqa: E402
from backtest.entry_policy import SignalPresentEntryPolicy  # noqa: E402
from core.enums import PortfolioMode, PositionSizeMethod, RebalanceFrequency  # noqa: E402
from core.types import SecurityId, Ticker  # noqa: E402
from data.loaders import ParquetLoader  # noqa: E402
from data.store import InMemoryDataStore  # noqa: E402
from entry_signals.examples.stub_entry_signal import ExampleStubEntrySignal  # noqa: E402
from exit_signals.examples.stub_exit_signal import ExampleStubExitSignal  # noqa: E402
from reporting.stores import (  # noqa: E402
    InMemoryResultStore,
    ParquetResultStore,
    ValidatingResultStore,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an example single-stock backtest")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Persist validated results as Parquet under this directory",
    )
    args = parser.parse_args()

    fixture_dir = ROOT / "tests" / "fixtures" / "data" / "mag7"
    if not fixture_dir.exists():
        raise SystemExit(f"Fixture dataset not found: {fixture_dir}")

    dataset = ParquetLoader().load(fixture_dir)
    store = InMemoryDataStore(dataset)

    config = SingleStockBacktestConfig(
        security_id=SecurityId("SEC_AAPL"),
        ticker=Ticker("AAPL"),
        start_date=date(2023, 1, 3),
        end_date=date(2024, 6, 28),
        initial_capital=100_000,
        slippage_pct=0.001,
        commission_pct=0.0,
        rebalance_frequency=RebalanceFrequency.MONTHLY,
        portfolio_mode=PortfolioMode.SINGLE,
        position_size_method=PositionSizeMethod.EQUAL_WEIGHT,
        experiment_name="example_aapl_stub_signals",
    )

    if args.output_dir is not None:
        result_store: InMemoryResultStore | ValidatingResultStore = ValidatingResultStore(
            ParquetResultStore(args.output_dir)
        )
    else:
        result_store = InMemoryResultStore()

    engine = SingleStockBacktestEngine()
    result = engine.run(
        config=config,
        data_access=store,
        entry_signal=ExampleStubEntrySignal(),
        exit_signal=ExampleStubExitSignal(max_holding_days=63),
        entry_policy=SignalPresentEntryPolicy(),
        result_store=result_store,
    )

    inner_store = (
        result_store.inner
        if isinstance(result_store, ValidatingResultStore)
        else result_store
    )
    if isinstance(inner_store, InMemoryResultStore):
        summary = inner_store.summary
        stock_summaries = inner_store.stock_summaries
    else:
        parquet_store = inner_store
        assert isinstance(parquet_store, ParquetResultStore)
        summary = parquet_store.load_backtest_summary(str(result.experiment_id))
        stock_summaries = parquet_store.load_stock_summaries(str(result.experiment_id))

    if summary is None:
        raise SystemExit("Backtest did not produce a summary")

    print(f"Experiment: {result.experiment_id}")
    print(f"Closed trades: {result.positions_closed}")
    print(f"Final portfolio value: {result.final_portfolio_value}")
    print(f"Total return: {summary.total_return}")
    print(f"Max drawdown: {summary.max_drawdown}")
    print(f"Sharpe ratio: {summary.sharpe_ratio}")
    print(f"Number of trades: {summary.number_of_trades}")
    if stock_summaries:
        stock_summary = stock_summaries[0]
        print(f"Stock net PnL: {stock_summary.total_net_pnl}")
        print(f"Stock win rate: {stock_summary.win_rate}")
    if args.output_dir is not None:
        print(f"Results persisted to: {args.output_dir / str(result.experiment_id)}")


if __name__ == "__main__":
    main()
