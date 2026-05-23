**Current Task:** Task 5: Update pyproject.toml, tests, README, run verification
Status: Complete

## What's Done
- Migrated docs/tier_1 → docs/requirements/ (6 core specs with v2_ prefix)
- Migrated config/ → configs/ with data, entry_signals, exit_signals, experiments subdirs
- Created data/cache/, experiments/, results/ subdirs
- Reorganized src/: schemas/, data/universe/, entry_signals/, exit_signals/, factors subdirs
- Added backtest engine/execution/position_sizing/statistics stubs
- Added evaluation/ and reporting/ modules
- Removed old modules: universe, entry, exit, portfolio, results (top-level)
- Updated CLAUDE.md, README, pyproject.toml, tests

## Next Steps
1. Commit changes

## Context
- Import examples: `from data.universe.protocols import UniverseBuilder`, `from schemas.entry import SignalMetadata`
- PortfolioConstructor moved to backtest/position_sizing.py
- ResultStore moved to reporting/protocols.py
- archive/ remains off limits
