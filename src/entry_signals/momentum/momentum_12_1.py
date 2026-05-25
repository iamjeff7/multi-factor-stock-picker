"""12-1 momentum entry signal."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from core.types import SecurityId, SignalId
from data.protocols import DataAccess
from entry_signals.base import BaseEntrySignal
from entry_signals.enums import MissingDataPolicy, SignalCategory
from schemas.data import PriceBar
from schemas.entry import SignalMetadata
from schemas.universe import UniverseMembership


class Momentum12_1EntrySignal(BaseEntrySignal):
    """Trailing return from lookback_days ending skip_days before evaluation."""

    DEFAULT_LOOKBACK_DAYS = 252
    DEFAULT_SKIP_DAYS = 21

    def __init__(
        self,
        *,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        skip_days: int = DEFAULT_SKIP_DAYS,
        missing_data_policy: MissingDataPolicy = MissingDataPolicy.EXCLUDE_SECURITY,
    ) -> None:
        if lookback_days <= 0:
            raise ValueError("lookback_days must be positive")
        if skip_days < 0:
            raise ValueError("skip_days must be non-negative")

        metadata = SignalMetadata(
            signal_id=SignalId("momentum_12_1"),
            signal_name="12-1 Momentum",
            signal_description=(
                "Adjusted-price return over lookback_days ending skip_days "
                "before the evaluation date"
            ),
            signal_category=SignalCategory.MOMENTUM,
            signal_version="1.0",
            missing_data_policy=missing_data_policy,
            higher_is_better=True,
        )
        super().__init__(metadata)
        self._lookback_days = lookback_days
        self._skip_days = skip_days

    @property
    def lookback_days(self) -> int:
        return self._lookback_days

    @property
    def skip_days(self) -> int:
        return self._skip_days

    def _compute_raw_value(
        self,
        evaluation_date: date,
        membership: UniverseMembership,
        data_access: DataAccess,
    ) -> Decimal | None:
        bars = self._load_price_history(
            data_access=data_access,
            security_id=membership.security_id,
            evaluation_date=evaluation_date,
        )
        if not bars:
            return None

        eval_index = _index_on_or_before(bars, evaluation_date)
        if eval_index is None:
            return None

        end_index = eval_index - self._skip_days
        start_index = end_index - self._lookback_days
        if start_index < 0 or end_index < 0:
            return None

        start_price = bars[start_index].adjusted_close
        end_price = bars[end_index].adjusted_close
        if start_price <= Decimal("0"):
            return None

        return (end_price / start_price) - Decimal("1")

    def _load_price_history(
        self,
        *,
        data_access: DataAccess,
        security_id: SecurityId,
        evaluation_date: date,
    ) -> list[PriceBar]:
        calendar_buffer = int((self._lookback_days + self._skip_days) * 1.5) + 30
        start_date = evaluation_date - timedelta(days=calendar_buffer)
        bars = data_access.get_prices(
            security_id=security_id,
            start_date=start_date,
            end_date=evaluation_date,
            as_of_date=evaluation_date,
        )
        eligible = [bar for bar in bars if bar.trade_date <= evaluation_date]
        return sorted(eligible, key=lambda bar: bar.trade_date)


def _index_on_or_before(bars: list[PriceBar], trade_date: date) -> int | None:
    eligible_indices = [index for index, bar in enumerate(bars) if bar.trade_date <= trade_date]
    if not eligible_indices:
        return None
    return eligible_indices[-1]
