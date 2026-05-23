# multi-factor-stock-picker

Multi-factor stock research framework.

## Structure

See `CLAUDE.md` for the canonical project layout.

Key import patterns:

```python
from data.protocols import DataAccess
from data.universe.protocols import UniverseBuilder
from entry_signals.protocols import EntrySignal
from schemas.entry import SignalMetadata
from reporting.protocols import ResultStore
```

## Setup

```bash
pip install -e ".[dev]"
```

## Verification

```bash
ruff check src/ tests/
mypy src/
pytest
```

## Configuration

Defaults in `configs/default.yaml`. Specs in `docs/requirements/`.

## AI tooling

Do not read `archive/`. See `CLAUDE.md` and `.cursor/rules/no-archive.mdc`.
