**Current Task:** Task 24: Extend research window / larger demo universe
Status: in progress

## What's Done
- Task 23: Top-N entry policy wired to factor scores
  - `TopNEntryPolicy`, `build_top_n_selections`, `score_cross_section` reuse
  - Experiment runner scores cross-section before backtest when `top_n` or factor eval enabled
  - Mag7 configs updated with `top_n: 2`
  - Tests pass (10 backtest tests)

## Next Steps
1. Extend Mag7 date range or add broader security fixture (≥30 names)
2. Add 21d IC horizon alongside 63d in demo configs
3. Verify IS/OOS IC split produces non-zero sample stability

## Context
- Top-N filters entries per rebalance date; each stock still runs an isolated single-position backtest
- `score_cross_section` results are reused by full factor evaluation to avoid duplicate scoring
