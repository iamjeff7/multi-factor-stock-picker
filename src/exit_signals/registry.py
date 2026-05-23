"""In-memory exit signal registry."""

from __future__ import annotations

from collections.abc import Sequence

from core.exceptions import ConfigurationError
from exit_signals.protocols import ExitSignal


class InMemoryExitSignalRegistry:
    """Registry for exit signal implementations."""

    def __init__(self) -> None:
        self._signals: dict[str, ExitSignal] = {}

    def register(self, signal: ExitSignal) -> None:
        signal_id = signal.signal_id
        if signal_id in self._signals:
            raise ConfigurationError(f"Exit signal already registered: {signal_id}")
        self._signals[signal_id] = signal

    def get(self, signal_id: str) -> ExitSignal:
        if signal_id not in self._signals:
            raise ConfigurationError(f"Exit signal not found: {signal_id}")
        return self._signals[signal_id]

    def list_enabled(self) -> Sequence[ExitSignal]:
        return list(self._signals.values())
