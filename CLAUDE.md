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
│   │   ├── v2_data_specification.md
│   │   ├── v2_universe_specification.md
│   │   ├── v2_entry_signal_specification.md
│   │   ├── v2_exit_signal_specification.md
│   │   ├── v2_backtest_methodology_specification.md
│   │   ├── v2_result_schema_specification.md
│   │   ├── v2_factor_scoring_specification.md
│   │   ├── v2_factor_combination_specification.md
│   │   ├── v2_information_coefficient_specification.md
│   │   ├── v2_factor_performance_specification.md
│   │   ├── v2_entry_robustness_scoring_specification.md
│   │   └── v2_exit_robustness_scoring_specification.md
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
