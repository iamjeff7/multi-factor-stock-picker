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
pytest tests/data/ -v
```

## Configuration

Defaults in `configs/default.yaml`. Specs in `docs/requirements/`.

## AI tooling

Do not read `archive/`. See `CLAUDE.md` and `.cursor/rules/no-archive.mdc`.
