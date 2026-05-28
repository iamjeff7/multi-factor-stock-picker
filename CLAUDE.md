# Project Instructions

## Archive folder

Never read, search, or reference any file under `archive/`. Use `docs/` for specifications.

## Code structure

- Shared infrastructure: `core`, `config` (under `src/`)
- Flat import style: `from data.protocols import DataAccess`, `from schemas.entry import SignalMetadata`
- Schemas: centralized in `src/schemas/`. Interfaces: `typing.Protocol`. No business logic in scaffolding phases.
- Specs live in `docs/requirements/`. Configs live in `configs/`.

## Project Structure

```
multi-factor-stock-picker/
├── docs/
│   ├── requirements/
│   │   ├── data_specification.md
│   │   ├── universe_specification.md
│   │   ├── entry_signal_specification.md
│   │   ├── exit_signal_specification.md
│   │   ├── backtest_methodology_specification.md
│   │   ├── result_schema_specification.md
│   │   ├── factor_scoring_specification.md
│   │   ├── factor_combination_specification.md
│   │   ├── information_coefficient_specification.md
│   │   ├── factor_performance_specification.md
│   │   ├── experiment_scoring_specification.md
│   │   ├── entry_robustness_scoring_specification.md
│   │   ├── exit_robustness_scoring_specification.md
│   │   └── combined_strategy_robustness_specification.md
│   │
│   └── experiments/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── cache/
│
├── src/
│   ├── core/
│   ├── config/
│   ├── schemas/
│   ├── data/
│   │   ├── loaders/
│   │   ├── universe/
│   │   ├── corporate_actions/
│   │   └── validation/
│   │
│   ├── entry_signals/
│   │   ├── momentum/
│   │   ├── value/
│   │   ├── quality/
│   │   └── ...
│   │
│   ├── exit_signals/
│   │   ├── stop_loss/
│   │   ├── trailing_stop/
│   │   ├── time_exit/
│   │   └── ...
│   │
│   ├── backtest/
│   │   ├── engine.py
│   │   ├── execution.py
│   │   ├── position_sizing.py
│   │   └── statistics.py
│   │
│   ├── factors/
│   │   ├── scoring/
│   │   ├── combination/
│   │   ├── ic/
│   │   └── performance/
│   │
│   ├── evaluation/
│   │   ├── entry/
│   │   ├── exit/
│   │   └── robustness/
│   │
│   └── reporting/
│       ├── templates/
│       └── generators/
│
├── experiments/
│   ├── entry/
│   │   ├── single_factor/
│   │   ├── multi_factor/
│   │   └── ranking/
│   │
│   └── exit/
│       ├── stop_loss/
│       ├── trailing_stop/
│       └── time_exit/
│
├── results/
│   ├── entry/
│   ├── exit/
│   ├── reports/
│   └── rankings/
│
├── configs/
│   ├── data/
│   ├── entry_signals/
│   ├── exit_signals/
│   └── experiments/
│
└── tests/
```

## Experiment scoring

See [`docs/requirements/experiment_scoring_specification.md`](docs/requirements/experiment_scoring_specification.md) for entry, exit, and combined metric weights and composite scores. Robustness dimensions are in the `*_robustness` specs under `docs/requirements/`.
