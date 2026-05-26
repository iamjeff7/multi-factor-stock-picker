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

## Task 23: Top-N entry policy
- Add `top_n` to experiment config; enter only when security is in top N by factor rank on rebalance date
- Reuse cross-sectional factor scores for both entry selection and factor evaluation
- `TopNEntryPolicy` requires non-null raw signal plus rank membership
- Tests for selection builder, entry policy, and experiment runner integration
- Update Mag7 momentum configs with `top_n: 2`

## Task 24: Extend research window / larger demo universe
- Run experiments on 2–3 years of data or add broader security set (≥30 names)
- Add shorter IC horizon (21d) alongside 63d where useful
- IS/OOS IC split and sample stability should produce non-zero scores

## Task 25: Factor performance module
- Implement `src/factors/performance/` per `v2_factor_performance_specification.md`
- Top/bottom quintile forward returns and long-short spread by rebalance date
- Add `factor_performance` section to experiment report

## Task 26: Complete entry robustness
- Implement rank stability (rank correlation across rebalance dates)
- Implement parameter stability (momentum lookback/skip sweeps)
- Wire regime and breadth when data supports them

## Task 27: Wire exit robustness into experiments
- Score exit stack from trade outcomes (IS/OOS)
- Add `exit_robustness` to experiment report

## Task 28: Universe builder in experiment runner
- Replace hardcoded YAML security lists with `DefaultUniverseBuilder` + liquidity filters

## Task 29: Documentation
- Update README with experiment run commands and report section descriptions

## Task 30: Factor combination in multi-factor experiments
- Wire `WeightedMeanFactorCombiner` into experiment flow for multi-factor runs

## Task 31: Housekeeping
- Log session to DEVLOG.md
- Add `src/research/` to pyproject.toml hatchling packages if needed
- Ensure full `pytest tests/` in CI
