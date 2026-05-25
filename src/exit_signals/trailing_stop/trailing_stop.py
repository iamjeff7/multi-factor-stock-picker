"""Trailing stop exit signal."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from core.exceptions import MissingSignalDataError
from core.types import SignalId
from data.protocols import DataAccess
from exit_signals.base import BaseExitSignal
from exit_signals.enums import ExitCategory, MissingDataPolicy
from exit_signals.price_access import get_close_on_date
from schemas.enums import EvaluationFrequency, ExitDecision
from schemas.exit import ExitSignalMetadata, PositionContext


class TrailingStopExitSignal(BaseExitSignal):
    """Exit when close falls trail_pct below the highest price since entry."""

    DEFAULT_TRAIL_PCT = Decimal("0.15")

    def __init__(
        self,
        *,
        trail_pct: Decimal = DEFAULT_TRAIL_PCT,
        missing_data_policy: MissingDataPolicy = MissingDataPolicy.HOLD_POSITION,
    ) -> None:
        if trail_pct <= Decimal("0") or trail_pct >= Decimal("1"):
            raise ValueError("trail_pct must be between 0 and 1")

        metadata = ExitSignalMetadata(
            signal_id=SignalId("trailing_stop"),
            signal_name="Trailing Stop",
            signal_description=(
                "Exit when close falls below highest_price_since_entry by trail_pct"
            ),
            signal_category=ExitCategory.TRAILING_STOP,
            signal_version="1.0",
            missing_data_policy=missing_data_policy,
            evaluation_frequency=EvaluationFrequency.DAILY,
        )
        super().__init__(metadata)
        self._trail_pct = trail_pct

    @property
    def trail_pct(self) -> Decimal:
        return self._trail_pct

    def _evaluate_condition(
        self,
        evaluation_date: date,
        position: PositionContext,
        market_data: DataAccess,
    ) -> tuple[ExitDecision, str | None]:
        if position.highest_price_since_entry is None:
            raise MissingSignalDataError("highest_price_since_entry unavailable")

        close = get_close_on_date(
            market_data,
            security_id=position.security_id,
            evaluation_date=evaluation_date,
        )
        stop_price = position.highest_price_since_entry * (Decimal("1") - self._trail_pct)
        if close <= stop_price:
            return (
                ExitDecision.EXIT,
                f"close {close} <= trailing_stop {stop_price} "
                f"(high {position.highest_price_since_entry}, trail_pct {self._trail_pct})",
            )
        return ExitDecision.HOLD, None
