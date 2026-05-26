# multi-factor-stock-picker

Multi-factor stock research framework.

## Structure

See `CLAUDE.md` for the canonical project layout.

## Setup

```bash
pip install -e ".[dev,data]"
```

## Example dataset (Mag 7)

Download AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA via yfinance:

```bash
python scripts/download_mag7_data.py --output data/raw/mag7_001
```

Generate synthetic edge-case fixtures for tests:

```bash
python scripts/generate_edge_case_data.py
```

## Data layer usage

```python
from pathlib import Path
from data.loaders import ParquetLoader
from data.store import InMemoryDataStore
from data.validation import DatasetValidator
from data.universe import DefaultUniverseBuilder
from datetime import date

dataset = ParquetLoader().load(Path("data/raw/mag7_001"))
store = InMemoryDataStore(dataset)

report = DatasetValidator().validate_all(dataset)
assert report.passed

snapshot = DefaultUniverseBuilder().build_membership(date(2024, 6, 3), store)
```

## Verification

```bash
ruff check src/ tests/ scripts/
mypy src/
pytest tests/ -v
```

## Single-stock backtest

Run one security with entry/exit signals and optional Parquet persistence:

```bash
python scripts/run_single_stock_backtest.py
python scripts/run_single_stock_backtest.py --output-dir results/single_stock_demo
```

## Unified experiments

Run entry, exit, or entry+exit experiments with a single CLI:

```bash
# Entry factor evaluation (demo = most recent complete trading year)
python scripts/run_experiment.py \
  --config configs/experiments/entry_demo.yaml \
  --output-dir results/entry_demo

# Exit factor evaluation
python scripts/run_experiment.py \
  --config configs/experiments/exit_demo.yaml \
  --output-dir results/exit_demo

# Extended Mag7 window (2005–2025 date range; requires matching data coverage)
python scripts/run_experiment.py \
  --config configs/experiments/entry_extended_demo.yaml \
  --output-dir results/entry_extended_demo

# Entry evaluation — oracle exit (best return within next 6 trading months)
python scripts/run_experiment.py \
  --config configs/experiments/entry_best_within_demo.yaml \
  --output-dir results/entry_best_within_demo

# Exit evaluation — bottom entry (lower-low + higher-low on close; look-ahead allowed)
python scripts/run_experiment.py \
  --config configs/experiments/exit_bottom_entry_demo.yaml \
  --output-dir results/exit_bottom_entry_demo

# Entry + exit combined (requires prior entry/exit ranking runs — see below)
pip install -e ".[research]"
python scripts/run_experiment.py \
  --config configs/experiments/entry_and_exit_demo.yaml \
  --output-dir results/entry_and_exit_demo
```

Use `--data` for the Parquet dataset (default: `tests/fixtures/data/mag7`) and
`--reference-date YYYY-MM-DD` to control demo preset resolution (defaults to today).

### Experiment modes

| Mode | Config field | Purpose |
|------|--------------|---------|
| `entry` | `experiment_mode: entry` | Sweep all real entry signals (+ variants); evaluate exits |
| `exit` | `experiment_mode: exit` | Sweep all real exit signals (+ variants); evaluate entries |
| `entry_and_exit` | `experiment_mode: entry_and_exit` | Combine ranked factors via VectorBT |

### Data presets

| Preset | Resolution |
|--------|------------|
| `demo` (default) | Most recent **complete calendar trading year** (e.g. 2025 when run in 2026) |
| `extended_demo` | Mag7, 2005-01-01 through 2025-12-31 |
| `full` | Reserved (2005–2025 broad universe; not available until data exists) |

### Entry experiment settings

**Fixed-period exit** (default — exit after N calendar months):

```yaml
entry:
  exit_evaluation_mode: fixed_period
  exit_horizons_months: [3]                   # default one horizon; use [1, 3, 6, 12] for all
  forward_window_trading_months: 6
```

**Best-within-fixed-period** (oracle — exit at max return within the forward window; look-ahead allowed):

```yaml
entry:
  exit_evaluation_mode: best_within_fixed_period
  exit_horizons_months: [3]                   # recorded in results; exit is oracle-based
  forward_window_trading_months: 6            # ~6 calendar months of trading days
```

Run: `configs/experiments/entry_best_within_demo.yaml`

### Exit experiment settings

**Fixed-period entry** (default — enter on a schedule):

```yaml
exit:
  entry_evaluation_mode: fixed_period
  entry_cadence: week                         # day | week | two_weeks | month
```

**Bottom entry** (lower-low + higher-low on close; look-ahead allowed):

```yaml
exit:
  entry_evaluation_mode: bottom_entry
  entry_cadence: week                         # ignored for bottom_entry; kept for schema compatibility
```

Run: `configs/experiments/exit_bottom_entry_demo.yaml`

### Ranking and selection

Factor scores use percentile-normalized metrics, configurable weights, and a robustness
penalty. Each segment (regime × cap × volume × volatility × liquidity) produces its own
ranking file with **95th-percentile voting** (not a fixed top-N).

Output files:

- Entry runs: `rankings/entry_top_factors.json`
- Exit runs: `rankings/exit_top_factors.json`

Metrics include `trades_per_trading_days`, `trades_per_month`, and `trades_per_trading_year`
(round trips only; aggregated).

### Entry + exit (VectorBT)

Requires optional dependencies and **ranking files from prior entry and exit runs**:

```bash
# 1. Produce ranking files (same data preset / reference date for all three runs)
python scripts/run_experiment.py \
  --config configs/experiments/entry_demo.yaml \
  --output-dir results/entry_demo

python scripts/run_experiment.py \
  --config configs/experiments/exit_demo.yaml \
  --output-dir results/exit_demo

# 2. Point combined config at your ranking outputs, e.g. in entry_and_exit_demo.yaml:
#    combined.entry_rankings_source: results/entry_demo/exp_<id>/rankings/entry_top_factors.json
#    combined.exit_rankings_source: results/exit_demo/exp_<id>/rankings/exit_top_factors.json

# 3. Run combined strategy
pip install -e ".[research]"
python scripts/run_experiment.py \
  --config configs/experiments/entry_and_exit_demo.yaml \
  --output-dir results/entry_and_exit_demo
```

Benchmark comparison uses SPY with T-bill risk-free rate. Each stock selects qualified
entry and exit factors from its segment using 95th-percentile voting weights.

### Experiment configs

| Config | Mode | Preset | Notes |
|--------|------|--------|-------|
| `entry_demo.yaml` | entry | demo | fixed-period exit (3 months) |
| `entry_best_within_demo.yaml` | entry | demo | oracle best-within-6-month exit |
| `entry_extended_demo.yaml` | entry | extended_demo | all horizons [1, 3, 6, 12] |
| `exit_demo.yaml` | exit | demo | fixed-period entry (weekly) |
| `exit_bottom_entry_demo.yaml` | exit | demo | bottom entry (LL+HL on close) |
| `entry_and_exit_demo.yaml` | entry_and_exit | demo | requires entry + exit ranking JSON paths |
| `mag7_stub_single_factor.yaml` | legacy stub smoke test | manual dates | |

`run_single_factor_experiment.py` and `run_multi_factor_experiment.py` are deprecated
wrappers that delegate to `run_experiment.py`.

### Output layout

```
results/<experiment_id>/
  rankings/entry_top_factors.json   # entry mode
  rankings/exit_top_factors.json      # exit mode
  reports/experiment_report.json
```

## Single-factor experiments (legacy)

Cross-sectional experiments run isolated per-stock backtests, aggregate mean return, and optionally score the entry factor (IC, robustness, quintile performance) plus exit robustness from closed trades.

```bash
# Stub signals on Mag7 (quick smoke test)
python scripts/run_single_factor_experiment.py \
  --config configs/experiments/mag7_stub_single_factor.yaml \
  --output-dir results/stub_demo
```

Note: legacy single-factor YAML configs use the old schema. Use unified configs above for new work.

```bash
# Real momentum 12-1 + exit stack, 2020–2024 (meaningful IS/OOS IC)
python scripts/run_single_factor_experiment.py \
  --config configs/experiments/mag7_momentum_12_1_extended.yaml \
  --output-dir results/extended_demo
```

Use `--data` to point at a Parquet dataset (default: `tests/fixtures/data/mag7`).

### Multi-factor experiments (legacy)

```bash
python scripts/run_multi_factor_experiment.py \
  --config configs/experiments/mag7_multi_momentum.yaml \
  --output-dir results/multi_factor_demo
```

### Experiment configs (legacy)

| Config | Purpose |
|--------|---------|
| `mag7_stub_single_factor.yaml` | Stub entry/exit, no factor evaluation |
| `mag7_momentum_12_1.yaml` | 2023 window, explicit tickers |
| `mag7_momentum_12_1_extended.yaml` | 2020–2024, factor eval + top-N entry |
| `mag7_momentum_12_1_universe.yaml` | Extended window, universe builder |
| `mag7_momentum_6_1.yaml` / `_extended.yaml` | 6-1 momentum variants |
| `mag7_multi_momentum.yaml` | Multi-factor 12-1 + 6-1 composite, top-N entry |

Key config fields:

- `securities` — explicit ticker list, or omit when using `universe`
- `universe` — price, liquidity, and history filters via `DefaultUniverseBuilder`
- `top_n` — enter only the top N names by factor rank on each rebalance date
- `factor_evaluation` — cross-sectional scoring, IC horizons, quintile performance
- `research` — IS/OOS split and degradation metrics when `sample_scope: FULL`

### Output layout (legacy)

Each run writes an immutable directory under `--output-dir`:

```
results/<experiment_id>/
  metadata/          # config snapshot, version metadata
  summaries/         # experiment + per-stock + IS/OOS summaries
  trades/            # closed trade records
  reports/
    experiment_report.json
```

Parquet tables hold Layer A signal/score records and Layer B stock summaries. The JSON report is the human-readable summary.

### Report sections (legacy)

`experiment_report.json` includes:

| Section | Description |
|---------|-------------|
| `experiment_metrics` | Pooled trade stats: mean stock return, win rate, trade count |
| `sample_metrics` | Same metrics split by IS and OOS when research scope is FULL |
| `is_to_oos_degradation` | Return and trade-count deltas across the canonical split |
| `factor_scoring` | Cross-sectional score counts and skipped dates |
| `factor_ic` | Spearman IC by horizon; IS/OOS IC summaries and degradation |
| `entry_robustness` | IC, return, sample, rank, and parameter stability scores |
| `factor_performance` | Quintile forward-return spreads and long-short premia |
| `factor_combination` | Multi-factor composite score summary (multi-factor runs only) |
| `exit_robustness` | Exit-stack stability from trade outcomes (performance, sample, holding period, distribution, risk) |

Pending dimensions (not yet scored) appear under `pending_dimensions` in the robustness sections.

## Configuration

Defaults in `configs/default.yaml`. Specs in `docs/requirements/`.

## AI tooling

Do not read `archive/`. See `CLAUDE.md` and `.cursor/rules/no-archive.mdc`.
