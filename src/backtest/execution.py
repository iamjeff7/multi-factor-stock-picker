"""Trade execution interfaces."""

from __future__ import annotations

from typing import Protocol

from core.enums import ExecutionPrice


class ExecutionModel(Protocol):
    """Defines how signals are translated into executable prices."""

    @property
    def execution_price(self) -> ExecutionPrice: ...
