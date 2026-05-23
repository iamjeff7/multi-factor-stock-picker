"""Entry signal interfaces."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Protocol

from data.protocols import DataAccess
from schemas.entry import EntrySignalResult, SignalMetadata
from schemas.universe import UniverseMembershipSnapshot


class EntrySignal(Protocol):
    """Produces raw ranking signal values for eligible securities."""

    @property
    def signal_id(self) -> str: ...

    @property
    def metadata(self) -> SignalMetadata: ...

    def calculate(
        self,
        evaluation_date: date,
        universe: UniverseMembershipSnapshot,
        data_access: DataAccess,
    ) -> Sequence[EntrySignalResult]: ...


class EntrySignalRegistry(Protocol):
    """Discovers and retrieves registered entry signals."""

    def register(self, signal: EntrySignal) -> None: ...

    def get(self, signal_id: str) -> EntrySignal: ...

    def list_enabled(self) -> Sequence[EntrySignal]: ...
