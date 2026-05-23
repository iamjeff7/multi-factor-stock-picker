## Global Guidelines
- Never read or reference anything under `archive/`
- Implement per `docs/requirements/v2_data_specification.md` and `v2_universe_specification.md`
- No entry/exit signals, no backtesting
- Point-in-time enforcement at the store layer
- Fundamentals NOT required for universe membership
- `min_market_cap` is optional (only when configured)
- Example dataset: AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA via yfinance

## Verification & Definition of Done
- `ruff check src/ tests/ scripts/`
- `mypy src/`
- `pytest tests/data/ -v` — all pass
- Download script produces Parquet under `data/raw/mag7_001/`

## Task 1: Dependencies and download
- Add optional `[data]` deps: pyarrow, pandas, yfinance
- `scripts/download_mag7_data.py` downloads 7 tickers to Parquet + manifest
- Commit `tests/fixtures/data/` subset for CI

## Task 2: Loading and store
- `DatasetManifest`, `ParquetLoader`, `LoadedDataset`
- `InMemoryDataStore` implements `DataAccess` with PIT filtering

## Task 3: Validation
- Price, volume, fundamental, corporate action validators
- `DatasetValidator` orchestrates all checks

## Task 4: Corporate actions
- PIT filter for actions
- `CorporateActionAdjuster` for splits/dividends

## Task 5: Universe
- ADDV liquidity (60-day window, data before eval date)
- Filters: exchange, type, price, history, delisting, optional market cap
- `DefaultUniverseBuilder`, `DefaultUniverseValidator`

## Task 6: Tests
- PIT access tests, validation tests, adjuster tests, universe tests
- Synthetic edge-case fixtures for delist/illiquid/IPO scenarios
