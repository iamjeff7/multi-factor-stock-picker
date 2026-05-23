## Global Guidelines
- Never read or reference anything under `archive/`
- Follow project structure in `CLAUDE.md`
- Flat import style under `src/`
- Schemas centralized in `src/schemas/`
- Specs in `docs/requirements/`, configs in `configs/`
- Use Pydantic v2 for schemas, `typing.Protocol` for interfaces
- No business logic in scaffolding phases

## Verification & Definition of Done
- `ruff check src/ tests/` — no errors
- `mypy src/` — passes
- Import smoke test passes (see tests/protocols/test_imports.py)
- Project layout matches `CLAUDE.md`

## Task 1: Docs migration
- Move tier_1 specs to `docs/requirements/` with v2_ prefix
- Create `docs/experiments/`

## Task 2: Config and top-level dirs
- Move `config/` → `configs/` with subdirs
- Create `data/cache/`, `experiments/`, `results/{entry,exit,reports,rankings}/`

## Task 3: src/ reorganization
- Create `src/schemas/` and consolidate all Pydantic models
- Nest universe under `src/data/universe/`
- Rename `entry/` → `entry_signals/`, `exit/` → `exit_signals/`
- Remove `src/portfolio/`, `src/results/` as top-level modules

## Task 4: New domains
- `src/factors/{scoring,combination,ic,performance}/`
- `src/backtest/{engine,execution,position_sizing,statistics}.py`
- `src/evaluation/{entry,exit,robustness}/`
- `src/reporting/{templates,generators}/`

## Task 5: Tooling
- Update pyproject.toml package list
- Update tests and README
- Run ruff, mypy, pytest
