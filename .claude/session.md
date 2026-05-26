**Current Task:** Task 35: Tests, README, replace old experiment scripts
Status: Complete

## What's Done
- Unified experiment framework under `src/experiments/`
- `scripts/run_experiment.py` + demo/extended configs
- Entry/exit runners with segmented 95th-percentile rankings
- Combined VectorBT runner (optional `.[research]` deps)
- README updated; legacy scripts delegate to new CLI
- Unit + integration tests in `tests/experiments/`

## Next Steps
1. Commit when ready
2. Optional: wire full robustness scoring (currently placeholder)
3. Optional: `full` data preset when broad dataset exists

## Context
- Demo = most recent complete calendar trading year
- Metrics: trades_per_trading_days, trades_per_month (no turnover_rate)
- Multi-position per ticker in trade simulator
