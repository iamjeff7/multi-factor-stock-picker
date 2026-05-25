"""Composite exit signal tests."""

from datetime import date

from core.types import SignalId
from data.protocols import DataAccess
from exit_signals.composite import CompositeExitSignalImpl
from exit_signals.enums import CompositeOperator, ExitCategory, MissingDataPolicy
from exit_signals.examples.stub_exit_signal import ExampleStubExitSignal
from schemas.enums import EvaluationFrequency, ExitDecision
from schemas.exit import ExitSignalMetadata, PositionContext


def test_composite_any_exits_when_one_child_exits(
    sample_position: PositionContext,
    mock_data_access: DataAccess,
) -> None:
    hold_signal = ExampleStubExitSignal(max_holding_days=500)
    exit_signal = ExampleStubExitSignal(max_holding_days=100)
    composite = CompositeExitSignalImpl(
        metadata=_composite_metadata(),
        signals=[hold_signal, exit_signal],
        operator=CompositeOperator.ANY,
    )

    result = composite.evaluate(date(2020, 6, 1), sample_position, mock_data_access)
    assert result.decision is ExitDecision.EXIT


def test_composite_all_holds_when_one_child_holds(
    sample_position: PositionContext,
    mock_data_access: DataAccess,
) -> None:
    hold_signal = ExampleStubExitSignal(max_holding_days=500)
    exit_signal = ExampleStubExitSignal(max_holding_days=100)
    composite = CompositeExitSignalImpl(
        metadata=_composite_metadata(),
        signals=[hold_signal, exit_signal],
        operator=CompositeOperator.ALL,
    )

    result = composite.evaluate(date(2020, 6, 1), sample_position, mock_data_access)
    assert result.decision is ExitDecision.HOLD


def test_composite_all_exits_when_all_children_exit(
    sample_position: PositionContext,
    mock_data_access: DataAccess,
) -> None:
    exit_a = ExampleStubExitSignal(max_holding_days=100)
    exit_b = ExampleStubExitSignal(max_holding_days=50)
    composite = CompositeExitSignalImpl(
        metadata=_composite_metadata(),
        signals=[exit_a, exit_b],
        operator=CompositeOperator.ALL,
    )

    result = composite.evaluate(date(2020, 6, 1), sample_position, mock_data_access)
    assert result.decision is ExitDecision.EXIT


def _composite_metadata() -> ExitSignalMetadata:
    return ExitSignalMetadata(
        signal_id=SignalId("composite_exit"),
        signal_name="Composite Exit",
        signal_category=ExitCategory.COMPOSITE_EXIT,
        signal_version="1.0",
        missing_data_policy=MissingDataPolicy.HOLD_POSITION,
        evaluation_frequency=EvaluationFrequency.DAILY,
    )
