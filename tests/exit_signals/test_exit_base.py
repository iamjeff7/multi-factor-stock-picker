"""Exit signal base class tests."""

from datetime import date

import pytest

from core.exceptions import MissingSignalDataError, ValidationError
from core.types import SignalId
from data.protocols import DataAccess
from exit_signals.base import BaseExitSignal
from exit_signals.enums import ExitCategory, MissingDataPolicy
from exit_signals.validator import ExitSignalValidator
from schemas.enums import EvaluationFrequency, ExitDecision
from schemas.exit import ExitSignalMetadata, PositionContext


class _RecordingExitSignal(BaseExitSignal):
    def __init__(
        self,
        metadata: ExitSignalMetadata,
        decision: ExitDecision,
        *,
        trigger_reason: str | None = None,
        raise_missing: bool = False,
    ) -> None:
        super().__init__(metadata)
        self._decision = decision
        self._trigger_reason = trigger_reason
        self._raise_missing = raise_missing

    def _evaluate_condition(
        self,
        evaluation_date: date,
        position: PositionContext,
        market_data: DataAccess,
    ) -> tuple[ExitDecision, str | None]:
        del evaluation_date, position, market_data
        if self._raise_missing:
            raise MissingSignalDataError("price unavailable")
        return self._decision, self._trigger_reason


def _metadata(policy: MissingDataPolicy) -> ExitSignalMetadata:
    return ExitSignalMetadata(
        signal_id=SignalId("test_exit"),
        signal_name="Test Exit",
        signal_category=ExitCategory.TIME_EXIT,
        signal_version="1.0",
        missing_data_policy=policy,
        evaluation_frequency=EvaluationFrequency.DAILY,
    )


def test_base_exit_signal_hold(
    sample_position: PositionContext,
    mock_data_access: DataAccess,
) -> None:
    signal = _RecordingExitSignal(_metadata(MissingDataPolicy.HOLD_POSITION), ExitDecision.HOLD)
    result = signal.evaluate(date(2020, 6, 1), sample_position, mock_data_access)
    assert result.decision is ExitDecision.HOLD


def test_base_exit_signal_exit_requires_reason(
    sample_position: PositionContext,
    mock_data_access: DataAccess,
) -> None:
    signal = _RecordingExitSignal(
        _metadata(MissingDataPolicy.HOLD_POSITION),
        ExitDecision.EXIT,
        trigger_reason="threshold reached",
    )
    result = signal.evaluate(date(2020, 6, 1), sample_position, mock_data_access)
    assert result.decision is ExitDecision.EXIT
    assert result.trigger_reason == "threshold reached"


def test_base_exit_signal_missing_data_hold_policy(
    sample_position: PositionContext,
    mock_data_access: DataAccess,
) -> None:
    signal = _RecordingExitSignal(
        _metadata(MissingDataPolicy.HOLD_POSITION),
        ExitDecision.HOLD,
        raise_missing=True,
    )
    result = signal.evaluate(date(2020, 6, 1), sample_position, mock_data_access)
    assert result.decision is ExitDecision.HOLD
    assert result.trigger_reason is not None


def test_base_exit_signal_missing_data_force_exit_policy(
    sample_position: PositionContext,
    mock_data_access: DataAccess,
) -> None:
    signal = _RecordingExitSignal(
        _metadata(MissingDataPolicy.FORCE_EXIT),
        ExitDecision.HOLD,
        raise_missing=True,
    )
    result = signal.evaluate(date(2020, 6, 1), sample_position, mock_data_access)
    assert result.decision is ExitDecision.EXIT


def test_base_exit_signal_skip_evaluation_raises(
    sample_position: PositionContext,
    mock_data_access: DataAccess,
) -> None:
    signal = _RecordingExitSignal(
        _metadata(MissingDataPolicy.SKIP_EVALUATION),
        ExitDecision.HOLD,
        raise_missing=True,
    )
    with pytest.raises(ValidationError, match="missing data"):
        signal.evaluate(date(2020, 6, 1), sample_position, mock_data_access)


def test_exit_signal_validator_rejects_evaluation_before_entry(
    sample_position: PositionContext,
) -> None:
    validator = ExitSignalValidator()
    report = validator.validate_inputs(date(2019, 12, 1), sample_position)
    assert report.passed is False
