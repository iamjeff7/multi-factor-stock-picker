"""Exit signal registry tests."""

import pytest

from core.exceptions import ConfigurationError
from exit_signals.examples.stub_exit_signal import ExampleStubExitSignal
from exit_signals.registry import InMemoryExitSignalRegistry


def test_registry_register_and_get() -> None:
    registry = InMemoryExitSignalRegistry()
    signal = ExampleStubExitSignal()
    registry.register(signal)

    assert registry.get("example_stub_exit") is signal
    registration = registry.get_registration("example_stub_exit")
    assert registration.enabled is True


def test_registry_duplicate_registration_raises() -> None:
    registry = InMemoryExitSignalRegistry()
    registry.register(ExampleStubExitSignal())

    with pytest.raises(ConfigurationError, match="already registered"):
        registry.register(ExampleStubExitSignal())


def test_registry_list_enabled_filters_disabled() -> None:
    registry = InMemoryExitSignalRegistry()
    signal = ExampleStubExitSignal()
    registry.register(signal, enabled=False)

    assert registry.list_enabled() == []
    registry.enable("example_stub_exit")
    assert len(registry.list_enabled()) == 1
