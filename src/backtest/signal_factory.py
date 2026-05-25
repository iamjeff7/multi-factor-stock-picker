"""Signal factory helpers for experiment scripts."""

from __future__ import annotations

from backtest.experiment_config import SignalConfig
from core.exceptions import ConfigurationError
from entry_signals.examples.stub_entry_signal import ExampleStubEntrySignal
from entry_signals.protocols import EntrySignal
from exit_signals.examples.stub_exit_signal import ExampleStubExitSignal
from exit_signals.protocols import ExitSignal


def build_entry_signal(config: SignalConfig) -> EntrySignal:
    if config.name == "example_stub":
        return ExampleStubEntrySignal()
    raise ConfigurationError(f"Unknown entry signal: {config.name}")


def build_exit_signal(config: SignalConfig) -> ExitSignal:
    if config.name == "example_stub_exit":
        max_holding_days = int(str(config.params.get("max_holding_days", 63)))
        return ExampleStubExitSignal(max_holding_days=max_holding_days)
    raise ConfigurationError(f"Unknown exit signal: {config.name}")
