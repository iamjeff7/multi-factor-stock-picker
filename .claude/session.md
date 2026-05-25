**Current Task:** Task 18: Reporting tests
Status: Complete

## What's Done
- Task 14: `StockSummaryRecord`, report schemas, PK helpers
- Task 15: `ResultSchemaValidator` with full record coverage
- Task 16: `InMemoryResultStore`, `ParquetResultStore`, `ValidatingResultStore`, aggregators
- Task 17: Engine persists config/version/stock summaries/manifest; script `--output-dir`
- Task 18: 15 new reporting tests + parquet integration test

## Verification (2026-05-25)
- `ruff check src/ tests/ scripts/` — pass
- `mypy src/` — pass
- `pytest tests/` — 69 passed
- `python scripts/run_single_stock_backtest.py` — 6 closed trades, stock summary printed

## Next Steps
1. Commit result persistence work
2. Factor pipeline (scoring, combination, IC, performance)

## Context
- `backtest/result_store.py` re-exports from `reporting.stores.memory`
- Parquet NaN/null round-trip handled in `reporting/serialization.py`
- Layer A signal/score storage ready for factor pipeline; Layer B populated by backtest
