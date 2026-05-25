## Global Guidelines
- Never read or reference anything under `archive/`
- Implement per `docs/requirements/v2_backtest_methodology_specification.md`
- Single-stock scope only (`PortfolioMode.SINGLE`); no factor scoring or ranking
- Reuse existing signal interfaces (`EntrySignal`, `ExitSignal`) and `DataAccess`
- Signal on T executes on T+1 (look-ahead protection per spec §7)
- Point-in-time data access only; failures halt execution (spec §21)

## Verification & Definition of Done
- `ruff check src/ tests/ scripts/`
- `mypy src/`
- `pytest tests/backtest/ -v` — all pass
- `python scripts/run_single_stock_backtest.py` — example run completes with summary output

## Task 8: Backtest config + portfolio state schemas
- Extend backtest config with `security_id`, `ticker`, `start_date`, `end_date`, sizing params
- Add runtime models: `PortfolioState`, `PendingOrder`, `OpenPosition`, `ClosedTrade`
- Entry policy protocol (converts raw signal → enter/hold without factor scoring)

## Task 9: Execution model + position sizer
- `NextBarExecutionModel` — NEXT_OPEN / NEXT_CLOSE / NEXT_VWAP fill prices from `DataAccess`
- Apply slippage and commission per spec §13–14
- `PositionSizer` implementations: `FixedDollarSizer`, `FullCapitalSizer` (single-stock equal weight)

## Task 10: SingleStockBacktestEngine + trade lifecycle
- Daily loop: entry eval on rebalance dates, exit eval daily when position open
- Queue orders on signal date T, execute on T+1
- Track position context (highest/lowest since entry, holding period, unrealized PnL)
- Handle delisting exits and split share adjustments
- Record trades, positions, portfolio snapshots, equity curve

## Task 11: Performance statistics calculator
- `DefaultPerformanceCalculator` from trades + equity curve
- Required metrics per spec §19: total return, CAGR, volatility, Sharpe, Sortino, max drawdown, Calmar, win rate, profit factor, avg trade, trade count, turnover

## Task 12: Backtest validator + in-memory result store
- `BacktestValidator` — cash/equity consistency, no negative shares, no future fills
- `InMemoryResultStore` for tests and example runs (implements `ResultStore` subset)

## Task 13: Tests + example run script
- Unit tests: execution pricing, slippage, sizing, entry/exit lifecycle, delisting, statistics
- Integration test on synthetic price series (deterministic, no network)
- `scripts/run_single_stock_backtest.py` using mag7 fixture + example signal stubs
