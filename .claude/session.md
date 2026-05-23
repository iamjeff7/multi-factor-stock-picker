**Current Task:** Data layer — complete, awaiting commit
Status: Complete

## What's Done
- ParquetLoader, InMemoryDataStore (PIT), DatasetValidator
- CorporateActionAdjuster, DefaultUniverseBuilder, DefaultUniverseValidator
- scripts/download_mag7_data.py (yfinance → Parquet)
- scripts/generate_edge_case_data.py (synthetic edge cases)
- tests/fixtures/data/mag7/ and edge_cases/
- tests/data/ — 11 tests; full suite 14 passing

## Verification (2026-05-23)
- `ruff check src/ tests/ scripts/` — pass
- `mypy src/` — pass
- `pytest tests/` — 14 passed

## Next Steps
1. Commit data layer changes (when requested)
2. Factor pipeline (scoring, combination, IC, performance) — not started

## Context
- Fundamentals not required for universe membership
- min_market_cap optional (null = skipped)
- Metadata uses point-in-time as_of_date rows (first + last trade date in download script)
- yfinance is demo-only; DataAccess abstracts storage
