**Current Task:** Task 25: Factor performance module
Status: in progress

## What's Done
- Task 23 committed (3d543d2): Top-N entry policy
- Task 24: Extended research window for meaningful IS/OOS IC
  - Added `mag7_momentum_12_1_extended.yaml` and `mag7_momentum_6_1_extended.yaml` (2020–2024)
  - Short Mag7 configs now include 21d + 63d IC horizons
  - Extended window produces IS/OOS IC and non-zero sample stability (~0.98)

## Next Steps
1. Implement quantile spread / long-short performance per spec
2. Add `factor_performance` section to experiment report

## Context
- Mag7 fixture already spans 2018–2026; 1-year demo configs kept for fast runs
- Extended configs use 60 monthly rebalance dates vs 12 in the 2023-only window
- Broader ≥30-name universe deferred; extended dates satisfy Task 24 acceptance criteria
