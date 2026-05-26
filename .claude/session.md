**Current Task:** Task 28: Universe builder in experiment runner
Status: in progress

## What's Done
- Task 27: Exit robustness wired into experiments
  - `compute_partial_exit_robustness` scores performance, sample, holding period, trade distribution, and risk from closed trades
  - IS/OOS sample stability from canonical split; regime and parameter pending
  - `exit_robustness` section added to experiment report

## Next Steps
1. Replace hardcoded YAML security lists with `DefaultUniverseBuilder`
2. Apply liquidity filters from universe config

## Context
- Extended Mag7 demo exit robustness uses real momentum_exit_stack trade outcomes
- Entry robustness score still persisted to Parquet; exit robustness is report-only for now
