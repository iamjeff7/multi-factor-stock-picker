**Current Task:** Task 30: Factor combination in multi-factor experiments
Status: Complete

## What's Done
- `MultiFactorExperimentConfig` with `entry_signals`, `factor_combination`, and shared universe/top_n settings
- `score_and_combine_multi_factor()` scores each factor and combines via `WeightedMeanFactorCombiner`
- `MultiFactorExperimentRunner` uses composite scores for top-N entry and persists composite + factor score Parquet
- `factor_combination` section added to experiment report
- Demo config `mag7_multi_momentum.yaml` and `scripts/run_multi_factor_experiment.py`
- Tests in `tests/backtest/test_multi_factor_experiment.py` (3 passing)
- README updated with multi-factor run command

## Next Steps
1. Commit changes
2. Task 31: Housekeeping (DEVLOG, pyproject, CI)

## Context
- Composite entry uses precomputed composite scores via `CompositeScoreEntrySignal`
- Demo: 84 composite scores across 12 rebalance dates for Mag7 2023 window
