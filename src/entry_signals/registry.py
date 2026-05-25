"""In-memory entry signal registry."""

from __future__ import annotations

from collections.abc import Sequence

from core.exceptions import ConfigurationError
from entry_signals.protocols import EntrySignal
from schemas.signals import SignalRegistration


class InMemoryEntrySignalRegistry:
    """Registry for entry signal implementations."""

    def __init__(self) -> None:
        self._signals: dict[str, EntrySignal] = {}
        self._registrations: dict[str, SignalRegistration] = {}

    def register(self, signal: EntrySignal, *, enabled: bool = True) -> None:
        signal_id = signal.signal_id
        if signal_id in self._signals:
            raise ConfigurationError(f"Entry signal already registered: {signal_id}")

        metadata = signal.metadata
        self._signals[signal_id] = signal
        self._registrations[signal_id] = SignalRegistration(
            signal_id=metadata.signal_id,
            signal_name=metadata.signal_name,
            signal_category=metadata.signal_category.value,
            signal_version=metadata.signal_version,
            enabled=enabled,
        )

    def enable(self, signal_id: str) -> None:
        registration = self.get_registration(signal_id)
        self._registrations[signal_id] = registration.model_copy(update={"enabled": True})

    def disable(self, signal_id: str) -> None:
        registration = self.get_registration(signal_id)
        self._registrations[signal_id] = registration.model_copy(update={"enabled": False})

    def get(self, signal_id: str) -> EntrySignal:
        if signal_id not in self._signals:
            raise ConfigurationError(f"Entry signal not found: {signal_id}")
        return self._signals[signal_id]

    def get_registration(self, signal_id: str) -> SignalRegistration:
        if signal_id not in self._registrations:
            raise ConfigurationError(f"Entry signal not found: {signal_id}")
        return self._registrations[signal_id]

    def list_all(self) -> Sequence[SignalRegistration]:
        return list(self._registrations.values())

    def list_enabled(self) -> Sequence[EntrySignal]:
        return [
            self._signals[registration.signal_id]
            for registration in self._registrations.values()
            if registration.enabled
        ]

    def list_disabled(self) -> Sequence[SignalRegistration]:
        return [
            registration
            for registration in self._registrations.values()
            if not registration.enabled
        ]
