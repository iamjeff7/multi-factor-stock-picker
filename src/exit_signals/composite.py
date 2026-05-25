"""Composite exit signal implementation."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from core.types import SignalId
from data.protocols import DataAccess
from exit_signals.enums import CompositeOperator
from exit_signals.protocols import ExitSignal
from schemas.enums import ExitDecision
from schemas.exit import ExitSignalMetadata, ExitSignalResult, PositionContext


class CompositeExitSignalImpl:
    """Combines multiple exit signals with ANY or ALL logic."""

    def __init__(
        self,
        metadata: ExitSignalMetadata,
        signals: Sequence[ExitSignal],
        operator: CompositeOperator,
    ) -> None:
        if not signals:
            raise ValueError("Composite exit signal requires at least one child signal")
        self._metadata = metadata
        self._signals = list(signals)
        self._operator = operator

    @property
    def signal_id(self) -> str:
        return str(self._metadata.signal_id)

    @property
    def metadata(self) -> ExitSignalMetadata:
        return self._metadata

    @property
    def operator(self) -> CompositeOperator:
        return self._operator

    @property
    def signals(self) -> Sequence[ExitSignal]:
        return self._signals

    def evaluate(
        self,
        evaluation_date: date,
        position: PositionContext,
        market_data: DataAccess,
    ) -> ExitSignalResult:
        child_results = [
            signal.evaluate(
                evaluation_date=evaluation_date,
                position=position,
                market_data=market_data,
            )
            for signal in self._signals
        ]

        exit_results = [result for result in child_results if result.decision is ExitDecision.EXIT]
        should_exit = (
            len(exit_results) > 0
            if self._operator is CompositeOperator.ANY
            else len(exit_results) == len(child_results)
        )

        if should_exit:
            reasons = [result.trigger_reason for result in exit_results if result.trigger_reason]
            trigger_reason = "; ".join(reasons) if reasons else "composite_exit_triggered"
            decision = ExitDecision.EXIT
        else:
            trigger_reason = None
            decision = ExitDecision.HOLD

        return ExitSignalResult(
            evaluation_date=evaluation_date,
            security_id=position.security_id,
            position_id=position.position_id,
            signal_id=SignalId(self.signal_id),
            signal_version=self._metadata.signal_version,
            decision=decision,
            trigger_reason=trigger_reason,
        )
