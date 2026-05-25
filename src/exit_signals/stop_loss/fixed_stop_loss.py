"""Fixed stop loss exit signal."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from core.types import SignalId
from data.protocols import DataAccess
from exit_signals.base import BaseExitSignal
from exit_signals.enums import ExitCategory, MissingDataPolicy
from exit_signals.price_access import get_close_on_date
from schemas.enums import EvaluationFrequency, ExitDecision
from schemas.exit import ExitSignalMetadata, PositionContext


class FixedStopLossExitSignal(BaseExitSignal):
    """Exit when close falls stop_pct below entry price."""

    DEFAULT_STOP_PCT = Decimal("0.10")

    def __init__(
        self,
        *,
        stop_pct: Decimal = DEFAULT_STOP_PCT,
        missing_data_policy: MissingDataPolicy = MissingDataPolicy.HOLD_POSITION,
    ) -> None:
        if stop_pct <= Decimal("0") or stop_pct >= Decimal("1"):
            raise ValueError("stop_pct must be between 0 and 1")

        metadata = ExitSignalMetadata(
            signal_id=SignalId("stop_loss"),
            signal_name="Fixed Stop Loss",
            signal_description="Exit when close falls below entry price by stop_pct",
            signal_category=ExitCategory.STOP_LOSS,
            signal_version="1.0",
            missing_data_policy=missing_data_policy,
            evaluation_frequency=EvaluationFrequency.DAILY,
        )
        super().__init__(metadata)
        self._stop_pct = stop_pct

    @property
    def stop_pct(self) -> Decimal:
        return self._stop_pct

    def _evaluate_condition(
        self,
        evaluation_date: date,
        position: PositionContext,
        market_data: DataAccess,
    ) -> tuple[ExitDecision, str | None]:
        close = get_close_on_date(
            market_data,
            security_id=position.security_id,
            evaluation_date=evaluation_date,
        )
        stop_price = position.entry_price * (Decimal("1") - self._stop_pct)
        if close <= stop_price:
            return (
                ExitDecision.EXIT,
                f"close {close} <= stop_price {stop_price} "
                f"(entry {position.entry_price}, stop_pct {self._stop_pct})",
            )
        return ExitDecision.HOLD, None
