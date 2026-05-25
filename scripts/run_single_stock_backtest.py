#!/usr/bin/env python3
"""Example single-stock backtest run."""

from __future__ import annotations

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
from backtest.result_store import InMemoryResultStore  # noqa: E402
from core.enums import PortfolioMode, PositionSizeMethod, RebalanceFrequency  # noqa: E402
from core.types import SecurityId, Ticker  # noqa: E402
from data.loaders import ParquetLoader  # noqa: E402
from data.store import InMemoryDataStore  # noqa: E402
from entry_signals.examples.stub_entry_signal import ExampleStubEntrySignal  # noqa: E402
from exit_signals.examples.stub_exit_signal import ExampleStubExitSignal  # noqa: E402


def main() -> None:
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

    summary = result_store.summary
    if summary is None:
        raise SystemExit("Backtest did not produce a summary")

    print(f"Experiment: {result.experiment_id}")
    print(f"Closed trades: {result.positions_closed}")
    print(f"Final portfolio value: {result.final_portfolio_value}")
    print(f"Total return: {summary.total_return}")
    print(f"Max drawdown: {summary.max_drawdown}")
    print(f"Sharpe ratio: {summary.sharpe_ratio}")
    print(f"Number of trades: {summary.number_of_trades}")


if __name__ == "__main__":
    main()
