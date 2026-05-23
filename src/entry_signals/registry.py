"""In-memory entry signal registry."""

from __future__ import annotations

from collections.abc import Sequence

from core.exceptions import ConfigurationError
from entry_signals.protocols import EntrySignal


class InMemoryEntrySignalRegistry:
    """Registry for entry signal implementations."""

    def __init__(self) -> None:
        self._signals: dict[str, EntrySignal] = {}

    def register(self, signal: EntrySignal) -> None:
        signal_id = signal.signal_id
        if signal_id in self._signals:
            raise ConfigurationError(f"Entry signal already registered: {signal_id}")
        self._signals[signal_id] = signal

    def get(self, signal_id: str) -> EntrySignal:
        if signal_id not in self._signals:
            raise ConfigurationError(f"Entry signal not found: {signal_id}")
        return self._signals[signal_id]

    def list_enabled(self) -> Sequence[EntrySignal]:
        return list(self._signals.values())
