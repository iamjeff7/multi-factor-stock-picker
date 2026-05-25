**Current Task:** Task 13: Tests + example run script
Status: Complete

## What's Done
- SingleStockBacktestConfig, PortfolioState, PendingOrder, OpenPosition
- EntryPolicy (SignalPresent, Threshold) — no factor scoring/ranking
- NextBarExecutionModel with slippage/commission
- FixedDollarSizer, FullCapitalSizer
- SingleStockBacktestEngine: T→T+1 entries/exits, splits, dividends, delisting
- DefaultPerformanceCalculator (spec §19 metrics)
- BacktestValidator, InMemoryResultStore
- 12 backtest tests; example script on mag7 AAPL

## Verification (2026-05-25)
- `ruff check src/ tests/ scripts/` — pass
- `mypy src/` — pass
- `pytest tests/` — 54 passed
- `python scripts/run_single_stock_backtest.py` — 6 closed trades, summary printed

## Next Steps
1. Commit backtest engine work
2. Factor pipeline (scoring, combination, IC, performance)

## Context
- portfolio_mode=SINGLE enforced in config
- Entry on rebalance dates; exit evaluated daily when position open
- Example uses ExampleStubEntrySignal + ExampleStubExitSignal (63-day hold)
