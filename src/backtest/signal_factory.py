"""Signal factory helpers for experiment scripts."""

from __future__ import annotations

from backtest.experiment_config import SignalConfig
from core.exceptions import ConfigurationError
from entry_signals.enums import MissingDataPolicy
from entry_signals.examples.stub_entry_signal import ExampleStubEntrySignal
from entry_signals.momentum.momentum_6_1 import Momentum6_1EntrySignal
from entry_signals.momentum.momentum_12_1 import Momentum12_1EntrySignal
from entry_signals.protocols import EntrySignal
from exit_signals.examples.stub_exit_signal import ExampleStubExitSignal
from exit_signals.protocols import ExitSignal


def build_entry_signal(config: SignalConfig) -> EntrySignal:
    if config.name == "example_stub":
        return ExampleStubEntrySignal()
    if config.name == "momentum_12_1":
        return Momentum12_1EntrySignal(
            lookback_days=int(str(config.params.get("lookback_days", 252))),
            skip_days=int(str(config.params.get("skip_days", 21))),
            missing_data_policy=_parse_missing_data_policy(config.params),
        )
    if config.name == "momentum_6_1":
        return Momentum6_1EntrySignal(
            lookback_days=int(str(config.params.get("lookback_days", 126))),
            skip_days=int(str(config.params.get("skip_days", 21))),
            missing_data_policy=_parse_missing_data_policy(config.params),
        )
    raise ConfigurationError(f"Unknown entry signal: {config.name}")


def _parse_missing_data_policy(params: dict[str, object]) -> MissingDataPolicy:
    raw = params.get("missing_data_policy")
    if raw is None:
        return MissingDataPolicy.EXCLUDE_SECURITY
    return MissingDataPolicy(str(raw))


def build_exit_signal(config: SignalConfig) -> ExitSignal:
    if config.name == "example_stub_exit":
        max_holding_days = int(str(config.params.get("max_holding_days", 63)))
        return ExampleStubExitSignal(max_holding_days=max_holding_days)
    raise ConfigurationError(f"Unknown exit signal: {config.name}")
