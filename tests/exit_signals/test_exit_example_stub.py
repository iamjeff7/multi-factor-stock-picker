"""Example exit signal stub tests."""

from datetime import date

from data.protocols import DataAccess
from exit_signals.examples.stub_exit_signal import ExampleStubExitSignal
from schemas.enums import ExitDecision
from schemas.exit import PositionContext


def test_example_stub_exit_signal_holds_before_threshold(
    sample_position: PositionContext,
    mock_data_access: DataAccess,
) -> None:
    signal = ExampleStubExitSignal(max_holding_days=252)
    result = signal.evaluate(date(2020, 6, 1), sample_position, mock_data_access)
    assert result.decision is ExitDecision.HOLD


def test_example_stub_exit_signal_exits_at_threshold(
    sample_position: PositionContext,
    mock_data_access: DataAccess,
) -> None:
    signal = ExampleStubExitSignal(max_holding_days=100)
    result = signal.evaluate(date(2020, 6, 1), sample_position, mock_data_access)
    assert result.decision is ExitDecision.EXIT
