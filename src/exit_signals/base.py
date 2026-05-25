"""Exit signal base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from core.exceptions import MissingSignalDataError, ValidationError
from core.types import SignalId
from data.protocols import DataAccess
from exit_signals.enums import MissingDataPolicy
from exit_signals.validator import ExitSignalValidator
from schemas.enums import ExitDecision
from schemas.exit import ExitSignalMetadata, ExitSignalResult, PositionContext


class BaseExitSignal(ABC):
    """Template-method base for exit signal implementations."""

    def __init__(
        self,
        metadata: ExitSignalMetadata,
        *,
        validator: ExitSignalValidator | None = None,
    ) -> None:
        self._metadata = metadata
        self._validator = validator or ExitSignalValidator()

    @property
    def signal_id(self) -> str:
        return str(self._metadata.signal_id)

    @property
    def metadata(self) -> ExitSignalMetadata:
        return self._metadata

    @property
    def missing_data_policy(self) -> MissingDataPolicy:
        return self._metadata.missing_data_policy

    def evaluate(
        self,
        evaluation_date: date,
        position: PositionContext,
        market_data: DataAccess,
    ) -> ExitSignalResult:
        self._validator.validate_inputs_or_raise(
            evaluation_date=evaluation_date,
            position=position,
        )

        try:
            decision, trigger_reason = self._evaluate_condition(
                evaluation_date=evaluation_date,
                position=position,
                market_data=market_data,
            )
        except MissingSignalDataError as exc:
            result = self._apply_missing_data_policy(
                evaluation_date=evaluation_date,
                position=position,
                reason=str(exc),
            )
            self._validator.validate_result_or_raise(result)
            return result

        result = self._build_result(
            evaluation_date=evaluation_date,
            position=position,
            decision=decision,
            trigger_reason=trigger_reason,
        )
        self._validator.validate_result_or_raise(result)
        return result

    @abstractmethod
    def _evaluate_condition(
        self,
        evaluation_date: date,
        position: PositionContext,
        market_data: DataAccess,
    ) -> tuple[ExitDecision, str | None]:
        """Evaluate the exit condition for one open position."""

    def _apply_missing_data_policy(
        self,
        evaluation_date: date,
        position: PositionContext,
        reason: str,
    ) -> ExitSignalResult:
        policy = self.missing_data_policy
        if policy is MissingDataPolicy.HOLD_POSITION:
            return self._build_result(
                evaluation_date=evaluation_date,
                position=position,
                decision=ExitDecision.HOLD,
                trigger_reason=f"missing_data: {reason}",
            )
        if policy is MissingDataPolicy.FORCE_EXIT:
            return self._build_result(
                evaluation_date=evaluation_date,
                position=position,
                decision=ExitDecision.EXIT,
                trigger_reason=f"missing_data: {reason}",
            )
        if policy is MissingDataPolicy.SKIP_EVALUATION:
            raise ValidationError(
                f"Exit signal {self.signal_id} cannot evaluate position due to missing data"
            )

        raise ValidationError(f"Unsupported missing-data policy: {policy}")

    def _build_result(
        self,
        evaluation_date: date,
        position: PositionContext,
        decision: ExitDecision,
        trigger_reason: str | None,
    ) -> ExitSignalResult:
        return ExitSignalResult(
            evaluation_date=evaluation_date,
            security_id=position.security_id,
            position_id=position.position_id,
            signal_id=SignalId(self.signal_id),
            signal_version=self._metadata.signal_version,
            decision=decision,
            trigger_reason=trigger_reason,
        )
