"""Backtesting engine interfaces and configuration."""

from backtest.calendar import is_rebalance_date, next_trading_day, trading_days_between
from backtest.config import BacktestConfig, SingleStockBacktestConfig
from backtest.engine import SingleStockBacktestEngine
from backtest.entry_policy import EntryPolicy, SignalPresentEntryPolicy, ThresholdEntryPolicy
from backtest.execution import ExecutionFill, NextBarExecutionModel
from backtest.position_sizing import (
    FixedDollarSizer,
    FullCapitalSizer,
    PositionSizer,
    build_position_sizer,
)
from backtest.result_store import InMemoryResultStore
from backtest.state import BacktestRunResult, PortfolioState
from backtest.statistics import DefaultPerformanceCalculator
from backtest.validator import BacktestValidator
from core.enums import ExecutionPrice, PortfolioMode, PositionSizeMethod, RebalanceFrequency

PerformanceCalculator = DefaultPerformanceCalculator

__all__ = [
    "BacktestConfig",
    "BacktestRunResult",
    "DefaultPerformanceCalculator",
    "EntryPolicy",
    "ExecutionFill",
    "ExecutionPrice",
    "FixedDollarSizer",
    "FullCapitalSizer",
    "InMemoryResultStore",
    "NextBarExecutionModel",
    "PerformanceCalculator",
    "PortfolioMode",
    "PortfolioState",
    "PositionSizeMethod",
    "PositionSizer",
    "RebalanceFrequency",
    "SignalPresentEntryPolicy",
    "SingleStockBacktestConfig",
    "SingleStockBacktestEngine",
    "ThresholdEntryPolicy",
    "BacktestValidator",
    "build_position_sizer",
    "is_rebalance_date",
    "next_trading_day",
    "trading_days_between",
]
