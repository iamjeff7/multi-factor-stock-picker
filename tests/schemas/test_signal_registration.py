"""Signal registration schema tests."""

from core.types import SignalId
from schemas.signals import SignalRegistration


def test_signal_registration_enabled_by_default() -> None:
    registration = SignalRegistration(
        signal_id=SignalId("example_stub"),
        signal_name="Example Stub",
        signal_category="MOMENTUM",
        signal_version="1.0",
    )
    assert registration.enabled is True
