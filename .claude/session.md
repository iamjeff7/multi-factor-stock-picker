**Current Task:** Task 22: Experiment runner tests
Status: Complete

## What's Done
- Committed result persistence (Session 5, d448dbc)
- Task 19–22: SingleFactorExperimentRunner with cross-stock aggregation
- ExperimentSummaryRecord, experiment aggregators, JSON report generator
- configs/experiments/mag7_stub_single_factor.yaml + run script
- 72 tests passing

## Verification (2026-05-25)
- `ruff check src/ tests/ scripts/` — pass
- `mypy src/` — pass
- `pytest tests/` — 72 passed
- `python scripts/run_single_factor_experiment.py --output-dir /tmp/mfsp_exp_test` — 7 stocks

## Next Steps
1. Commit experiment runner work
2. Factor pipeline (scoring, combination, IC, performance)

## Context
- Runner uses one parent experiment_id; per-stock engine runs with result_store=None
- Experiment metrics are cross-sectional (mean stock return), not combined portfolio
- Skips stocks when engine raises "No trading days available"
- Config snapshot dict fields JSON-encoded for Parquet compatibility
