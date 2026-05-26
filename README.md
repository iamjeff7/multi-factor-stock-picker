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

## Single-factor experiments

Cross-sectional experiments run isolated per-stock backtests, aggregate mean return, and optionally score the entry factor (IC, robustness, quintile performance) plus exit robustness from closed trades.

```bash
# Stub signals on Mag7 (quick smoke test)
python scripts/run_single_factor_experiment.py \
  --config configs/experiments/mag7_stub_single_factor.yaml \
  --output-dir results/stub_demo

# Real momentum 12-1 + exit stack, 2020–2024 (meaningful IS/OOS IC)
python scripts/run_single_factor_experiment.py \
  --config configs/experiments/mag7_momentum_12_1_extended.yaml \
  --output-dir results/extended_demo

# Same setup, securities resolved from universe filters instead of a YAML list
python scripts/run_single_factor_experiment.py \
  --config configs/experiments/mag7_momentum_12_1_universe.yaml \
  --output-dir results/universe_demo
```

Use `--data` to point at a Parquet dataset (default: `tests/fixtures/data/mag7`).

### Experiment configs

| Config | Purpose |
|--------|---------|
| `mag7_stub_single_factor.yaml` | Stub entry/exit, no factor evaluation |
| `mag7_momentum_12_1.yaml` | 2023 window, explicit tickers |
| `mag7_momentum_12_1_extended.yaml` | 2020–2024, factor eval + top-N entry |
| `mag7_momentum_12_1_universe.yaml` | Extended window, universe builder |
| `mag7_momentum_6_1.yaml` / `_extended.yaml` | 6-1 momentum variants |

Key config fields:

- `securities` — explicit ticker list, or omit when using `universe`
- `universe` — price, liquidity, and history filters via `DefaultUniverseBuilder`
- `top_n` — enter only the top N names by factor rank on each rebalance date
- `factor_evaluation` — cross-sectional scoring, IC horizons, quintile performance
- `research` — IS/OOS split and degradation metrics when `sample_scope: FULL`

### Output layout

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

### Report sections

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
| `exit_robustness` | Exit-stack stability from trade outcomes (performance, sample, holding period, distribution, risk) |

Pending dimensions (not yet scored) appear under `pending_dimensions` in the robustness sections.

## Configuration

Defaults in `configs/default.yaml`. Specs in `docs/requirements/`.

## AI tooling

Do not read `archive/`. See `CLAUDE.md` and `.cursor/rules/no-archive.mdc`.
