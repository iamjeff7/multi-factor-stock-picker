"""Example entry signal stub tests."""

from datetime import date

from data.protocols import DataAccess
from entry_signals.enums import MissingDataPolicy
from entry_signals.examples.stub_entry_signal import ExampleStubEntrySignal
from schemas.universe import UniverseMembershipSnapshot


def test_example_stub_entry_signal_returns_finite_values(
    sample_universe_snapshot: UniverseMembershipSnapshot,
    mock_data_access: DataAccess,
) -> None:
    signal = ExampleStubEntrySignal()
    results = signal.calculate(date(2020, 1, 31), sample_universe_snapshot, mock_data_access)

    assert len(results) == 2
    assert all(result.raw_signal_value is not None for result in results)


def test_example_stub_entry_signal_exclude_missing(
    sample_universe_snapshot: UniverseMembershipSnapshot,
    mock_data_access: DataAccess,
) -> None:
    signal = ExampleStubEntrySignal(
        missing_data_policy=MissingDataPolicy.EXCLUDE_SECURITY,
        return_none_for_security_suffix="200",
    )
    results = signal.calculate(date(2020, 1, 31), sample_universe_snapshot, mock_data_access)

    assert len(results) == 1
    assert str(results[0].security_id) == "100"
