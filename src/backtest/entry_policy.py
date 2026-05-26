"""Entry decision policies for single-stock backtests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Protocol

from core.types import SecurityId
from schemas.entry import EntrySignalResult, SignalMetadata


class EntryPolicy(Protocol):
    """Converts a raw entry signal into an enter/hold decision."""

    def should_enter(self, signal: EntrySignalResult | None) -> bool: ...


class SignalPresentEntryPolicy:
    """Enter when the entry signal produced a non-null raw value."""

    def should_enter(self, signal: EntrySignalResult | None) -> bool:
        return signal is not None and signal.raw_signal_value is not None


class ThresholdEntryPolicy:
    """Enter when raw signal crosses a configured threshold."""

    def __init__(self, metadata: SignalMetadata, threshold: Decimal) -> None:
        self._metadata = metadata
        self._threshold = threshold

    def should_enter(self, signal: EntrySignalResult | None) -> bool:
        if signal is None or signal.raw_signal_value is None:
            return False
        value = signal.raw_signal_value
        if self._metadata.higher_is_better:
            return value >= self._threshold
        return value <= self._threshold


class TopNEntryPolicy:
    """Enter when the security is in the top-N cross-sectional selection for that date."""

    def __init__(self, selections_by_date: dict[date, set[SecurityId]]) -> None:
        self._selections_by_date = selections_by_date

    def should_enter(self, signal: EntrySignalResult | None) -> bool:
        if signal is None or signal.raw_signal_value is None:
            return False
        selected = self._selections_by_date.get(signal.evaluation_date)
        if selected is None:
            return False
        return signal.security_id in selected
