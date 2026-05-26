**Current Task:** Task 26: Complete entry robustness (rank + parameter stability first)
Status: in progress

## What's Done
- Task 25: Factor performance module
  - `FactorPerformanceCalculator` with quintile spreads and long-short returns
  - IS/OOS performance summaries in experiment report (`factor_performance` section)
  - Mag7 configs use quintiles (5) for 7-stock demo universe
  - Slimmed package `__init__.py` files to break circular imports

## Next Steps
1. Implement rank stability (rank correlation across rebalance dates)
2. Implement parameter stability (momentum lookback/skip sweeps)

## Context
- Extended demo: mean Q5-Q1 spread ~13.4% at 63d horizon, 61% spread win rate
- Performance uses same forward returns as IC analysis on primary horizon
