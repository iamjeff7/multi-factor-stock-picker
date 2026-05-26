"""Signal factory helpers for experiment scripts."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from backtest.experiment_config import SignalConfig
from core.exceptions import ConfigurationError
from core.types import SignalId
from entry_signals.enums import MissingDataPolicy
from entry_signals.examples.stub_entry_signal import ExampleStubEntrySignal
from entry_signals.momentum.momentum_6_1 import Momentum6_1EntrySignal
from entry_signals.momentum.momentum_12_1 import Momentum12_1EntrySignal
from entry_signals.protocols import EntrySignal
from exit_signals.composite import CompositeExitSignalImpl
from exit_signals.enums import CompositeOperator, ExitCategory
from exit_signals.enums import MissingDataPolicy as ExitMissingDataPolicy
from exit_signals.examples.stub_exit_signal import ExampleStubExitSignal
from exit_signals.protocols import ExitSignal
from exit_signals.stop_loss.fixed_stop_loss import FixedStopLossExitSignal
from exit_signals.trailing_stop.trailing_stop import TrailingStopExitSignal
from schemas.enums import EvaluationFrequency
from schemas.exit import ExitSignalMetadata


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


def build_entry_signals(configs: Sequence[SignalConfig]) -> list[EntrySignal]:
    return [build_entry_signal(config) for config in configs]


def _parse_missing_data_policy(params: dict[str, object]) -> MissingDataPolicy:
    raw = params.get("missing_data_policy")
    if raw is None:
        return MissingDataPolicy.EXCLUDE_SECURITY
    return MissingDataPolicy(str(raw))


def build_exit_signal(config: SignalConfig) -> ExitSignal:
    if config.name == "example_stub_exit":
        max_holding_days = int(str(config.params.get("max_holding_days", 63)))
        return ExampleStubExitSignal(max_holding_days=max_holding_days)
    if config.name == "stop_loss":
        return FixedStopLossExitSignal(
            stop_pct=_decimal_param(config.params, "stop_pct", "0.10"),
            missing_data_policy=_parse_exit_missing_data_policy(config.params),
        )
    if config.name == "trailing_stop":
        return TrailingStopExitSignal(
            trail_pct=_decimal_param(config.params, "trail_pct", "0.15"),
            missing_data_policy=_parse_exit_missing_data_policy(config.params),
        )
    if config.name == "momentum_exit_stack":
        stop_pct = _decimal_param(config.params, "stop_pct", "0.10")
        trail_pct = _decimal_param(config.params, "trail_pct", "0.15")
        missing_data_policy = _parse_exit_missing_data_policy(config.params)
        return CompositeExitSignalImpl(
            metadata=ExitSignalMetadata(
                signal_id=SignalId("momentum_exit_stack"),
                signal_name="Momentum Exit Stack",
                signal_description="Fixed stop loss OR trailing stop (whichever triggers first)",
                signal_category=ExitCategory.COMPOSITE_EXIT,
                signal_version="1.0",
                missing_data_policy=missing_data_policy,
                evaluation_frequency=EvaluationFrequency.DAILY,
            ),
            signals=[
                FixedStopLossExitSignal(
                    stop_pct=stop_pct,
                    missing_data_policy=missing_data_policy,
                ),
                TrailingStopExitSignal(
                    trail_pct=trail_pct,
                    missing_data_policy=missing_data_policy,
                ),
            ],
            operator=CompositeOperator.ANY,
        )
    raise ConfigurationError(f"Unknown exit signal: {config.name}")


def _decimal_param(params: dict[str, object], key: str, default: str) -> Decimal:
    raw = params.get(key, default)
    return Decimal(str(raw))


def _parse_exit_missing_data_policy(params: dict[str, object]) -> ExitMissingDataPolicy:
    raw = params.get("missing_data_policy")
    if raw is None:
        return ExitMissingDataPolicy.HOLD_POSITION
    return ExitMissingDataPolicy(str(raw))
