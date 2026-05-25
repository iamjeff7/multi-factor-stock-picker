"""Entry signal registry tests."""

import pytest

from core.exceptions import ConfigurationError
from entry_signals.examples.stub_entry_signal import ExampleStubEntrySignal
from entry_signals.registry import InMemoryEntrySignalRegistry


def test_registry_register_and_get() -> None:
    registry = InMemoryEntrySignalRegistry()
    signal = ExampleStubEntrySignal()
    registry.register(signal)

    assert registry.get("example_stub") is signal
    registration = registry.get_registration("example_stub")
    assert registration.enabled is True
    assert registration.signal_name == "Example Stub Entry Signal"


def test_registry_duplicate_registration_raises() -> None:
    registry = InMemoryEntrySignalRegistry()
    signal = ExampleStubEntrySignal()
    registry.register(signal)

    with pytest.raises(ConfigurationError, match="already registered"):
        registry.register(ExampleStubEntrySignal())


def test_registry_enable_disable() -> None:
    registry = InMemoryEntrySignalRegistry()
    signal = ExampleStubEntrySignal()
    registry.register(signal, enabled=False)

    assert registry.list_enabled() == []
    assert len(registry.list_disabled()) == 1

    registry.enable("example_stub")
    assert len(registry.list_enabled()) == 1
    assert registry.list_disabled() == []

    registry.disable("example_stub")
    assert registry.list_enabled() == []
    assert registry.get("example_stub") is signal
