## Global Guidelines
- Never read or reference anything under `archive/`
- Implement per `docs/requirements/v2_result_schema_specification.md`
- Validate all outputs against schemas before persistence
- Parquet preferred format; immutable experiment directories
- Stock results: Layer A (per-security signal/score records) + Layer B (StockSummaryRecord)

## Verification & Definition of Done
- `ruff check src/ tests/ scripts/`
- `mypy src/`
- `pytest tests/ -v` — all pass
- `python scripts/run_single_stock_backtest.py` — example run completes with summary output
- `python scripts/run_single_stock_backtest.py --output-dir /tmp/exp_test` — Parquet persistence

## Task 14: Result schemas
- Add `StockSummaryRecord`, `ReportArtifactRecord`, `ExperimentReportManifest`
- Add primary key helpers in `reporting/keys.py`
- Tests in `tests/schemas/test_results.py`

## Task 15: Validation layer
- `ResultSchemaValidator` with schema, referential, and consistency checks
- Cross-check `validate_stock_summary_matches_trades`
- Extend `SchemaValidator` protocol to all record types

## Task 16: Storage layer
- `InMemoryResultStore` (complete, moved to `reporting/stores/`)
- `ParquetResultStore` with immutable writes and read-back loaders
- `ValidatingResultStore` wrapper
- `aggregate_stock_summaries` in `reporting/aggregators.py`

## Task 17: Engine integration
- Persist config snapshot, version metadata, stock summaries, report manifest
- Example script supports `--output-dir` for Parquet persistence

## Task 18: Tests
- `tests/reporting/` — validator, memory store, parquet store, aggregators
- `tests/backtest/test_engine.py` — parquet integration test
