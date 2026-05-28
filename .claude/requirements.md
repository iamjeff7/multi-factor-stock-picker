## Global Guidelines
- Never read or reference anything under `archive/`
- Specs live in `docs/requirements/` (no `v2_` prefix)
- Validate outputs against schemas before persistence
- Experiment directories are immutable once written
- Demo data (Mag7) is for CI only; research tasks use the broad downloaded dataset

## Verification & Definition of Done
- `ruff check src/ tests/ scripts/`
- `mypy src/`
- `pytest tests/ -v`
- Task-specific commands listed per task below

## Task 1: Download and validate a broad research dataset
- Add or extend a download script for a universe of ≥30 liquid US equities (not just Mag7)
- Cover a multi-year window suitable for IS/OOS (e.g. 2005–2025 or last N complete calendar years)
- Write Parquet + manifest under `data/raw/` with price, volume, metadata, and corporate actions where available
- Run `DatasetValidator` on the new dataset; document path and date range in README
- Commit test fixtures only if needed for CI smoke tests (keep large raw data out of git if appropriate)

## Task 2: Enable `full` data preset and experiment configs
- Implement `DataPreset.FULL` in `src/experiments/data_presets.py` (currently raises not available)
- Add `configs/experiments/*_full.yaml` pointing at the new dataset
- README documents how to run entry/exit/combined with `data_preset: full`

## Task 3: Run end-to-end entry → exit → combined experiments on real data
- Run entry experiment → `rankings/entry_top_factors.json`
- Run exit experiment → `rankings/exit_top_factors.json`
- Run combined experiment using both ranking files
- Verify new scoring metrics appear in reports (`final_factor_score`, `final_strategy_score`, ranking breakdowns)
- Acceptance: all three modes complete without error on the broad dataset

## Task 4: Complete pending entry/exit robustness dimensions
- Entry: implement `market_regime_consistency`, `data_perturbation_resilience`; finish `parameter_sensitivity` in partial path
- Exit: implement `market_regime_consistency`, `parameter_sensitivity`, `data_perturbation_resilience`
- Regime classification inputs must be documented (even if simple bull/bear/sideways proxy)
- Pending dimension lists shrink; overall robustness uses finalized weights from specs

## Task 5: Implement combined strategy robustness scorer
- Replace stub in `src/evaluation/combined/robustness/scorer.py`
- Score all eight dimensions from `combined_strategy_robustness_specification.md`
- Wire into combined runner report payload (not score 0 / all pending)

## Task 6: Wire combined benchmark metrics and final strategy score
- Resolve benchmark ticker (e.g. SPY) to prices via `DataAccess` or explicit benchmark security config
- Populate alpha, beta, tail_ratio, turnover_efficiency in combined reports
- `final_strategy_score` reflects non-trivial robustness when Task 5 is done

## Task 7: Persist unified experiment parquet artifacts
- Entry/exit/combined runners write trades, stock summaries, and layout paths listed in report `source_artifacts`
- Outputs validate via `ResultSchemaValidator`
- JSON reports remain; parquet is no longer aspirational-only

## Task 8: Add IS/OOS/FULL trade-level summaries to entry and exit experiments
- Per spec: separate IS/OOS/FULL backtest/experiment summaries for trade simulation metrics
- Use canonical 80/20 trading-day split from `research/sample_split.py`
- Report payloads include degradation where spec requires it

## Task 9: Wire multi-factor combination into unified experiments
- Connect `WeightedMeanFactorCombiner` to unified `run_experiment.py` (or document explicit non-goal)
- Multi-factor entry ranking path produces composite scores before segment ranking
- Config + test for at least one multi-factor entry demo

## Task 10: Expand real signal catalog
- Add at least one non-momentum entry signal and one non-stop exit signal under category folders
- Register in signal factory / `signal_catalog` for experiment sweeps
- Tests cover new signals in trade simulator paths
