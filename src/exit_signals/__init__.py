"""Exit signal definitions and registry."""

from exit_signals.enums import CompositeOperator, ExitCategory, ExitDecision, MissingDataPolicy
from exit_signals.protocols import CompositeExitSignal, ExitSignal, ExitSignalRegistry
from exit_signals.registry import InMemoryExitSignalRegistry

__all__ = [
    "CompositeExitSignal",
    "CompositeOperator",
    "ExitCategory",
    "ExitDecision",
    "ExitSignal",
    "ExitSignalRegistry",
    "InMemoryExitSignalRegistry",
    "MissingDataPolicy",
]
