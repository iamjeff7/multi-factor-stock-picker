**Current Task:** Task 27: Wire exit robustness into experiments
Status: in progress

## What's Done
- Task 26: Rank + parameter entry robustness wired into experiments
  - Rank stability from consecutive-date factor score correlations and top-group persistence
  - Parameter stability from momentum lookback ±20% IC sweep
  - Pending dimensions reduced to regime + breadth only
  - Extended demo: rank ~0.86, parameter ~0.66, overall ACCEPTABLE

## Next Steps
1. Wire ExitRobustnessScorer from trade outcomes
2. Add exit_robustness section to experiment report

## Context
- Robustness weights renormalize over 5 active dimensions (ic, return, sample, rank, parameter)
- Parameter sweep re-scores cross-section 3x (80%/100%/120% lookback) — noticeable runtime cost
