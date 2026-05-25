**Current Task:** Task 7: Signal interfaces
Status: Complete

## What's Done
- Schema extensions: SignalRegistration, missing_data_policy on metadata, EvaluationFrequency
- BaseEntrySignal + EntrySignalValidator (template method, missing-data policies)
- BaseExitSignal + ExitSignalValidator + CompositeExitSignalImpl
- InMemory registries with enabled/disabled tracking (get() always returns)
- Example stubs under entry_signals/examples/ and exit_signals/examples/
- 28 new tests; full suite 42 passing

## Verification (2026-05-25)
- `ruff check src/ tests/` — pass
- `mypy src/` — pass
- `pytest tests/` — 42 passed

## Next Steps
1. Factor pipeline (scoring, combination, IC, performance)
2. Real signal implementations (momentum, stop loss, etc.)

## Context
- SKIP_EVALUATION missing-data policy raises ValidationError (never silent)
- get() returns disabled signals; list_enabled() filters
- Category folders (momentum/, stop_loss/) remain empty stubs
