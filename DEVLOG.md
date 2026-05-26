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

## Session 5 — 2026-05-25 19:13:29

- Goal: Implement validated result persistence per v2_result_schema_specification.md

- What I Built:
  - `src/reporting/stores/` — InMemoryResultStore, ParquetResultStore, ValidatingResultStore
  - `src/reporting/validator.py` — ResultSchemaValidator for all record types
  - `src/reporting/aggregators.py` — StockSummaryRecord derivation from trades
  - `src/reporting/serialization.py` — Parquet round-trip with null handling
  - `src/schemas/results.py` — StockSummaryRecord, report manifest schemas
  - `src/backtest/engine.py` — persists config, version, stock summaries, manifest
  - `scripts/run_single_stock_backtest.py` — `--output-dir` for Parquet persistence
  - `tests/reporting/` — validator, store, aggregator tests (15 tests)

- Decisions Made:
  - ValidatingResultStore wraps any store — validate-then-write per spec §20
  - Parquet store rejects overwrites — immutability per spec §3.1
  - Layer B stock summaries derived post-backtest; Layer A storage ready for factor pipeline
  - Report manifest stored as artifact rows, not nested single Parquet row

- What Didn't Work:
  - Parquet NaN/null round-trip required explicit NaN→None in deserialization

- Tasks Completed:
  - Task 14: Result schemas
  - Task 15: Validation layer
  - Task 16: Storage layer
  - Task 17: Engine integration
  - Task 18: Reporting tests

## Session 6 — 2026-05-25 19:25:00

- Goal: Build cross-sectional single-factor experiment orchestration

- What I Built:
  - `src/backtest/experiment_runner.py` — SingleFactorExperimentRunner with per-stock capital reset
  - `src/backtest/experiment_config.py` — SingleFactorExperimentConfig + YAML loading
  - `src/reporting/experiment_aggregators.py` — trade, stock, experiment metric aggregation
  - `src/reporting/generators/experiment_report.py` — JSON experiment report
  - `scripts/run_single_factor_experiment.py` — mag7 example experiment
  - `configs/experiments/mag7_stub_single_factor.yaml` — example config

- Decisions Made:
  - One parent experiment_id; per-stock runs skip individual persistence
  - Experiment return metrics are cross-sectional across stocks, not combined portfolio
  - Nested config dicts JSON-encoded in Parquet serialization

- What Didn't Work:
  - Empty SignalConfig params dict broke Parquet struct serialization (fixed via JSON encoding)

- Tasks Completed:
  - Task 19–22: Experiment runner, aggregators, report, tests

## Session 7 — 2026-05-25 21:59:03

- Goal: Build factor evaluation pipeline and canonical IS/OOS validation framework

- What I Built:
  - `src/factors/scoring/`, `combination/`, `ic/` — factor scoring, combination, and IC modules
  - `src/evaluation/robustness/`, `exit/robustness/` — entry and exit robustness scorers
  - `src/research/` — trading-day 80/20 IS/OOS split, enforcement, and degradation metrics
  - `src/backtest/experiment_runner.py` — dual IS/OOS experiment summaries and reporting
  - `docs/requirements/` — updated specs for validation framework, IC, robustness, and result schemas

- Decisions Made:
  - One full backtest run with post-hoc IS/OOS metric split — trades by exit_date, IC by evaluation_date
  - DISCOVERY phase hard-errors on OOS access; demo configs use one-year Mag7 window

- What Didn't Work:
  - none

- Tasks Completed:
  - Factor pipeline (scoring, combination, IC, robustness)
  - IS/OOS validation framework and spec alignment

## Session 8 — 2026-05-26 12:13:01

- Goal: Complete demo experiment pipeline — universe builder, docs, multi-factor combination, and CI

- What I Built:
  - `src/backtest/universe_resolution.py` — resolve experiment securities from `DefaultUniverseBuilder`
  - `src/backtest/multi_factor_experiment_config.py`, `factor_combination_flow.py`, `multi_factor_experiment_runner.py` — multi-factor experiments with weighted-mean composite ranks
  - `src/backtest/composite_entry_signal.py` — top-N entry from precomputed composite scores
  - `configs/experiments/mag7_momentum_12_1_universe.yaml`, `mag7_multi_momentum.yaml` — universe and multi-factor demo configs
  - `scripts/run_multi_factor_experiment.py` — multi-factor experiment CLI
  - `.github/workflows/ci.yml` — ruff, mypy, and full pytest on push/PR
  - `README.md` — experiment run commands, output layout, and report section docs

- Decisions Made:
  - Universe resolution at `start_date`; `top_n` validated after resolve, not against `minimum_security_count`
  - Multi-factor backtests use composite score lookup for entry; per-factor scores persisted separately
  - Factor evaluation IC/robustness remains single-factor path; multi-factor runs focus on combination + top-N

- What Didn't Work:
  - Initial multi-factor tests failed on default `minimum_security_count=30` with Mag7 — fixed via demo config override to 7

- Tasks Completed:
  - Task 28: Universe builder in experiment runner
  - Task 29: README experiment runs + report sections
  - Task 30: Factor combination in multi-factor experiments
  - Task 31: Housekeeping (DEVLOG, pyproject research package, CI)

## Session 11 — 2026-05-26 19:28:47

- Goal: Add unified entry, exit, and entry+exit experiment framework with segmented factor rankings and VectorBT combined runs

- What I Built:
  - `src/experiments/` — config, data presets, metrics, segments, ranking, trade simulator, entry/exit/combined runners
  - `scripts/run_experiment.py` — single CLI for entry, exit, and entry_and_exit modes
  - `configs/experiments/` — entry_demo, exit_demo, entry_extended_demo, entry_best_within_demo, exit_bottom_entry_demo, entry_and_exit_demo
  - `tests/experiments/` — metrics, ranking, data presets, runner integration, combined signal tests
  - `README.md` — run commands for all experiment modes including best-within-period, bottom entry, and entry+exit
  - `pyproject.toml` — experiments package and optional `[research]` vectorbt deps

- Decisions Made:
  - Demo preset uses most recent complete calendar trading year, not rolling 252 days
  - Rankings use 95th-percentile voting per segment with trades_per_trading_days and trades_per_month metrics
  - Combined runner reads prior ranking JSON; signal_catalog accepts SignalConfig or SignalVariant for entry+exit builds

- What Didn't Work:
  - entry_and_exit failed with `'SignalConfig' object has no attribute 'config'` — fixed by accepting SignalConfig in signal_catalog builders
  - pytest collection failed when `tests/experiments/__init__.py` shadowed `src/experiments` — removed test package init

- Tasks Completed:
  - Task 32: Unified experiment framework (schemas, presets, metrics, segments, ranking)
  - Task 33: Entry/exit evaluation runners + trade simulator
  - Task 34: Entry+Exit VectorBT runner + run_experiment.py
  - Task 35: Tests, README, replace old experiment scripts
