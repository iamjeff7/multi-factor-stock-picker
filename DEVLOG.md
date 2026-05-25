# DEVLOG

## Session 1 — 2026-05-23 21:40:20

- Goal: Scaffold the multi-factor stock research framework to match CLAUDE.md project structure

- What I Built:
  - `src/` — flat modules: core, config, schemas, data, entry_signals, exit_signals, factors, backtest, evaluation, reporting
  - `src/schemas/` — centralized Pydantic models for all domains
  - `src/data/universe/` — universe construction protocols nested under data
  - `configs/` — YAML defaults for data, universe, backtest, and signal configs
  - `docs/requirements/` — six core v2 specification documents
  - `pyproject.toml` — hatchling package layout, ruff, mypy, pytest
  - `CLAUDE.md`, `.cursorignore`, `.cursor/rules/no-archive.mdc` — project and AI tooling rules
  - `.claude/tasks.md`, `requirements.md`, `session.md` — task workflow files
  - `tests/` — schema and protocol import smoke tests

- Decisions Made:
  - Centralized shared enums in `schemas/enums.py` — avoids circular imports between data, entry_signals, and exit_signals
  - Moved `PortfolioConstructor` to `backtest/position_sizing.py` and `ResultStore` to `reporting/` — matches CLAUDE.md layout
  - Kept `core/` and `config/` as shared infrastructure even though not shown in the tree diagram
  - Excluded `archive/` from git — not source of truth for specs

- What Didn't Work:
  - Initial `schemas/__init__.py` eager re-exports caused circular import through entry_signals/exit_signals — fixed by slim __init__ and shared enums

- Tasks Completed:
  - Task 1: Reconcile CLAUDE.md and migrate docs to docs/requirements/
  - Task 2: Migrate config/ to configs/ and create top-level dirs
  - Task 3: Reorganize src/ — schemas, data/universe, entry_signals, exit_signals
  - Task 4: Add factors subdirs, backtest stubs, evaluation, reporting
  - Task 5: Update pyproject.toml, tests, README, run verification

## Session 2 — 2026-05-23 22:04:26

- Goal: Implement the data and universe layer per v2_data and v2_universe specifications — loading, validation, PIT access, and universe construction (no signals or backtesting)

- What I Built:
  - `src/data/loaders/` — DatasetManifest, ParquetLoader, LoadedDataset
  - `src/data/store/in_memory_store.py` — InMemoryDataStore with point-in-time enforcement
  - `src/data/validation/` — price, volume, fundamentals, corporate action validators; DatasetValidator orchestrator
  - `src/data/corporate_actions/` — CorporateActionAdjuster and PIT filter for splits/dividends
  - `src/data/universe/` — DefaultUniverseBuilder, ADDV liquidity, filters, DefaultUniverseValidator
  - `scripts/download_mag7_data.py` — yfinance download for Mag 7 tickers to Parquet + manifest
  - `scripts/generate_edge_case_data.py` — synthetic delist/illiquid/IPO fixtures
  - `tests/fixtures/data/mag7/` and `edge_cases/` — committed Parquet fixtures for CI
  - `tests/data/` — 11 tests covering PIT access, validation, adjuster, universe, Mag 7 integration
  - `pyproject.toml`, `README.md` — pyarrow/pandas/yfinance deps and usage docs

- Decisions Made:
  - PIT enforcement at InMemoryDataStore — rejects future-dated queries and filters prices, fundamentals, and corporate actions by as-of date
  - Metadata uses two as_of_date rows per ticker (first and last trade date) — historical eval dates resolve correctly
  - Fundamentals not required for universe membership — min_market_cap filter optional (null skips)
  - yfinance is demo-only — DataAccess protocol abstracts storage for production datasets
  - Exchange code mapping in download script (NMS/NCM/NGM → NASDAQ, etc.) — yfinance returns non-standard codes

- What Didn't Work:
  - Metadata as_of_date only at dataset end — Mag 7 tests failed on historical eval dates; fixed with first+last trade date rows
  - Price filter on non-trading eval dates — passes_price_filter now uses last bar on or before eval date
  - Edge-case fixture date range too short for 252-day history filter — extended generator to 1300 days
  - Circular imports from eager schema re-exports — already fixed in Session 1; no recurrence in data layer

- Tasks Completed:
  - Task 1: Add data deps, download script, Mag 7 Parquet dataset
  - Task 2: ParquetLoader + DatasetManifest + InMemoryDataStore (PIT)
  - Task 3: Dataset validation (price, volume, fundamentals, corporate actions)
  - Task 4: Corporate action adjuster + PIT filter
  - Task 5: DefaultUniverseBuilder + liquidity + validator (optional market cap)
  - Task 6: Unit tests, edge-case fixtures, verification


## Session 3 — 2026-05-25 18:15:28

- Goal: Implement entry/exit signal interfaces per v2 specs — base classes, validation, registry, and example stubs (no real signals)

- What I Built:
  - `src/entry_signals/base.py` — BaseEntrySignal template method with missing-data policies
  - `src/entry_signals/validator.py` — EntrySignalValidator for inputs and batch outputs
  - `src/entry_signals/examples/stub_entry_signal.py` — deterministic example stub
  - `src/exit_signals/base.py` — BaseExitSignal with MissingSignalDataError handling
  - `src/exit_signals/validator.py` — ExitSignalValidator for position inputs and EXIT/HOLD outputs
  - `src/exit_signals/composite.py` — CompositeExitSignalImpl (ANY/ALL)
  - `src/exit_signals/examples/stub_exit_signal.py` — time-threshold example stub
  - `src/schemas/signals.py` — SignalRegistration with enabled flag
  - `src/entry_signals/registry.py`, `src/exit_signals/registry.py` — enable/disable tracking
  - `tests/entry_signals/`, `tests/exit_signals/` — 28 new tests; shared fixtures in tests/conftest.py

- Decisions Made:
  - get() returns disabled signals; list_enabled() filters — registry lookup stays stable
  - SKIP_EVALUATION missing-data policy raises ValidationError — failures never silent per spec
  - Example stubs live under examples/ — category folders (momentum/, stop_loss/) remain empty
  - Non-finite raw values rejected in BaseEntrySignal before Pydantic model construction

- What Didn't Work:
  - Duplicate test module names across entry_signals/ and exit_signals/ — pytest import collision; renamed exit test files with exit_ prefix

- Tasks Completed:
  - Task 7: Signal interfaces (entry/exit base, validation, registry, examples, tests)

## Session 4 — 2026-05-25 18:42:24

- Goal: Implement single-stock backtest engine per v2 backtest methodology — entries, exits, sizing, trade lifecycle, statistics (no factor scoring/ranking)

- What I Built:
  - `src/backtest/engine.py` — SingleStockBacktestEngine with T→T+1 execution loop
  - `src/backtest/config.py` — SingleStockBacktestConfig (portfolio_mode=SINGLE enforced)
  - `src/backtest/execution.py` — NextBarExecutionModel with slippage and commission
  - `src/backtest/position_sizing.py` — FixedDollarSizer and FullCapitalSizer
  - `src/backtest/entry_policy.py` — SignalPresentEntryPolicy and ThresholdEntryPolicy
  - `src/backtest/lifecycle.py` — order queue, open/close trades, split adjustment
  - `src/backtest/statistics.py` — DefaultPerformanceCalculator (spec §19 metrics)
  - `src/backtest/validator.py`, `src/backtest/result_store.py` — integrity checks and in-memory persistence
  - `scripts/run_single_stock_backtest.py` — example AAPL run on mag7 fixtures
  - `tests/backtest/` — 12 tests with synthetic price series fixtures

- Decisions Made:
  - EntryPolicy replaces factor ranking for single-stock scope — raw signal + policy only
  - Entry evaluated on rebalance dates; exit evaluated daily when position is open
  - Signal on T executes on T+1 — look-ahead protection per spec §7
  - Delisting forces exit; splits adjust share count and entry price in lifecycle

- What Didn't Work:
  - none

- Tasks Completed:
  - Task 8: Backtest config + portfolio state schemas
  - Task 9: Execution model + position sizer
  - Task 10: SingleStockBacktestEngine + trade lifecycle
  - Task 11: Performance statistics calculator
  - Task 12: Backtest validator + in-memory result store
  - Task 13: Tests + example run script
