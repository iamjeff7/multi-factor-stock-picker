"""Example exit signal stub for interface demonstration."""

from __future__ import annotations

from datetime import date

from core.types import SignalId
from data.protocols import DataAccess
from exit_signals.base import BaseExitSignal
from exit_signals.enums import ExitCategory, MissingDataPolicy
from schemas.enums import EvaluationFrequency, ExitDecision
from schemas.exit import ExitSignalMetadata, PositionContext


class ExampleStubExitSignal(BaseExitSignal):
    """Time-based stub that exits when holding period exceeds a threshold."""

    def __init__(
        self,
        *,
        max_holding_days: int = 252,
        missing_data_policy: MissingDataPolicy = MissingDataPolicy.HOLD_POSITION,
    ) -> None:
        metadata = ExitSignalMetadata(
            signal_id=SignalId("example_stub_exit"),
            signal_name="Example Stub Exit Signal",
            signal_description="Demonstrates BaseExitSignal without real market logic",
            signal_category=ExitCategory.TIME_EXIT,
            signal_version="1.0",
            missing_data_policy=missing_data_policy,
            evaluation_frequency=EvaluationFrequency.DAILY,
        )
        super().__init__(metadata)
        self._max_holding_days = max_holding_days

    def _evaluate_condition(
        self,
        evaluation_date: date,
        position: PositionContext,
        market_data: DataAccess,
    ) -> tuple[ExitDecision, str | None]:
        del evaluation_date, market_data

        if position.holding_period >= self._max_holding_days:
            return (
                ExitDecision.EXIT,
                f"holding_period {position.holding_period} >= {self._max_holding_days}",
            )
        return ExitDecision.HOLD, None
