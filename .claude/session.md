**Current Task:** Task 1: Download and validate a broad research dataset (multi-year, ≥30 names)
Status: in progress

## What's Done
- Prior work through Task 35 is complete (unified experiments, scoring spec alignment, spec rename)
- Mag7 demo dataset + fixtures exist for CI
- Experiment scoring specs and entry/exit/combined ranking framework implemented

## Next Steps
1. Decide target universe (e.g. S&P 500 liquid subset, custom ticker list) and date range
2. Extend or add download script under `scripts/`
3. Validate with `DatasetValidator` and document dataset path in README

## Context
- `scripts/download_mag7_data.py` is demo-only (7 tickers, yfinance)
- `DataPreset.FULL` is stubbed — blocked until a broad dataset exists
- Combined alpha/beta and combined robustness still depend on richer data and Task 4–6
- Ranking/scoring refactor is done; next bottleneck is data coverage and robustness depth
