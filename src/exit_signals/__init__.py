"""Exit signal definitions and registry."""

from exit_signals.base import BaseExitSignal
from exit_signals.composite import CompositeExitSignalImpl
from exit_signals.enums import CompositeOperator, ExitCategory, ExitDecision, MissingDataPolicy
from exit_signals.protocols import CompositeExitSignal, ExitSignal, ExitSignalRegistry
from exit_signals.registry import InMemoryExitSignalRegistry
from exit_signals.validator import ExitSignalValidator

__all__ = [
    "BaseExitSignal",
    "CompositeExitSignal",
    "CompositeExitSignalImpl",
    "CompositeOperator",
    "ExitCategory",
    "ExitDecision",
    "ExitSignal",
    "ExitSignalRegistry",
    "ExitSignalValidator",
    "InMemoryExitSignalRegistry",
    "MissingDataPolicy",
]
