**Current Task:** Task 28: Universe builder in experiment runner
Status: Complete

## What's Done
- Added `universe: UniverseSettings | None` to `SingleFactorExperimentConfig`; securities list optional when universe is set
- Created `src/backtest/universe_resolution.py` with `resolve_experiment_securities`, `with_resolved_securities`, and `demo_universe_settings`
- Experiment runner resolves universe at `start_date` via `DefaultUniverseBuilder` before backtests run
- Added `configs/experiments/mag7_momentum_12_1_universe.yaml` (no hardcoded tickers)
- Tests: resolution from Mag7 fixture, top_n validation, runner integration (7/7 securities)
- Demo run verified: `python scripts/run_single_factor_experiment.py --config configs/experiments/mag7_momentum_12_1_universe.yaml`
- All verification checks passed for Task 28 files

## Next Steps
1. Commit changes

## Context
- Universe resolution uses `start_date` as evaluation date for membership
- `top_n` validated after resolve; explicit securities path unchanged
- Factor evaluation `minimum_security_count` still enforced at evaluation time, not during resolution
