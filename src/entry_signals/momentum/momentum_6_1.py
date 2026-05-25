"""6-1 momentum entry signal."""

from __future__ import annotations

from core.types import SignalId
from entry_signals.enums import MissingDataPolicy
from entry_signals.momentum.trailing_momentum import TrailingMomentumEntrySignal


class Momentum6_1EntrySignal(TrailingMomentumEntrySignal):
    """Trailing return over 126 trading days ending 21 days before evaluation."""

    DEFAULT_LOOKBACK_DAYS = 126
    DEFAULT_SKIP_DAYS = 21

    def __init__(
        self,
        *,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        skip_days: int = DEFAULT_SKIP_DAYS,
        missing_data_policy: MissingDataPolicy = MissingDataPolicy.EXCLUDE_SECURITY,
    ) -> None:
        super().__init__(
            signal_id=SignalId("momentum_6_1"),
            signal_name="6-1 Momentum",
            signal_description=(
                "Adjusted-price return over lookback_days ending skip_days "
                "before the evaluation date"
            ),
            lookback_days=lookback_days,
            skip_days=skip_days,
            missing_data_policy=missing_data_policy,
        )
