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

Each entry experiment runs **two evaluation layers** for every signal variant:

1. **Cross-section analytics** — IC, quantile performance, and entry robustness via `SingleFactorFactorEvaluator`
2. **Trade simulation** — per-stock metrics with a standardized exit protocol

Cross-section results appear under `cross_section` in each `factor_results` row. Rankings use
real robustness scores when cross-section evaluation completes.

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

**Cross-section evaluation** (runs automatically unless disabled):

```yaml
factor_evaluation:
  enabled: true
  minimum_security_count: 30   # capped to universe size at runtime
  primary_horizon: 63
  horizons: [21, 63]
  compute_robustness: true

research:
  research_mode: DEMO
  research_phase: VALIDATION
  sample_scope: FULL
```

### Exit experiment settings

Each exit experiment runs **two evaluation layers** for every signal variant:

1. **Trade simulation** — per-stock metrics with a standardized entry protocol
2. **Exit robustness** — pooled trade outcomes scored via `compute_partial_exit_robustness`

Exit robustness results appear under `exit_robustness` in each `factor_results` row. Rankings
use real robustness scores when evaluation completes.

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

**Exit robustness** (runs automatically unless disabled):

```yaml
exit:
  compute_robustness: true

research:
  research_mode: DEMO
  research_phase: VALIDATION
  sample_scope: FULL
```

### Ranking and selection

Factor scores use percentile-normalized metrics, configurable weights, and a robustness
penalty. Each segment (regime × cap × volume × volatility × liquidity) produces its own
ranking file with **95th-percentile voting** (not a fixed top-N).

Rankings include an `evaluation_summary` inside each factor's `score_breakdown`:
- Entry runs: `mean_ic`, `mean_spread`, `overall_robustness_score`
- Exit runs: `overall_robustness_score`, `performance_stability_score`

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

### Output layout

```
results/<experiment_id>/
  rankings/entry_top_factors.json   # entry mode
  rankings/exit_top_factors.json      # exit mode
  reports/experiment_report.json
```

Unified experiment reports include cross-section factor evaluation sections built in
`reporting/factor_evaluation_payload.py`.

## Configuration

Defaults in `configs/default.yaml`. Specs in `docs/requirements/`.

## AI tooling

Do not read `archive/`. See `CLAUDE.md` and `.cursor/rules/no-archive.mdc`.
