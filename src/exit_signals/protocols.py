"""Exit signal interfaces."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Protocol

from data.protocols import DataAccess
from exit_signals.enums import CompositeOperator
from schemas.exit import ExitSignalMetadata, ExitSignalResult, PositionContext


class ExitSignal(Protocol):
    """Evaluates whether an open position should be closed."""

    @property
    def signal_id(self) -> str: ...

    @property
    def metadata(self) -> ExitSignalMetadata: ...

    def evaluate(
        self,
        evaluation_date: date,
        position: PositionContext,
        market_data: DataAccess,
    ) -> ExitSignalResult: ...


class CompositeExitSignal(Protocol):
    """Combines multiple exit signals with ANY or ALL logic."""

    @property
    def operator(self) -> CompositeOperator: ...

    @property
    def signals(self) -> Sequence[ExitSignal]: ...

    def evaluate(
        self,
        evaluation_date: date,
        position: PositionContext,
        market_data: DataAccess,
    ) -> ExitSignalResult: ...


class ExitSignalRegistry(Protocol):
    """Discovers and retrieves registered exit signals."""

    def register(self, signal: ExitSignal) -> None: ...

    def get(self, signal_id: str) -> ExitSignal: ...

    def list_enabled(self) -> Sequence[ExitSignal]: ...
