"""Shared schema enumerations."""

from enum import StrEnum


class RobustnessGrade(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


class SignalCategory(StrEnum):
    MOMENTUM = "MOMENTUM"
    TREND = "TREND"
    VALUE = "VALUE"
    QUALITY = "QUALITY"
    GROWTH = "GROWTH"
    PROFITABILITY = "PROFITABILITY"
    VOLATILITY = "VOLATILITY"
    LIQUIDITY = "LIQUIDITY"
    SENTIMENT = "SENTIMENT"
    ANALYST = "ANALYST"
    TECHNICAL = "TECHNICAL"
    FUNDAMENTAL = "FUNDAMENTAL"


class EntryMissingDataPolicy(StrEnum):
    EXCLUDE_SECURITY = "exclude_security"
    ASSIGN_NULL = "assign_null"
    ASSIGN_DEFAULT_VALUE = "assign_default_value"


class SignalDirection(StrEnum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


class ExitCategory(StrEnum):
    STOP_LOSS = "STOP_LOSS"
    TRAILING_STOP = "TRAILING_STOP"
    PROFIT_TARGET = "PROFIT_TARGET"
    TIME_EXIT = "TIME_EXIT"
    TREND_EXIT = "TREND_EXIT"
    MOVING_AVERAGE_EXIT = "MOVING_AVERAGE_EXIT"
    VOLATILITY_EXIT = "VOLATILITY_EXIT"
    DRAWDOWN_EXIT = "DRAWDOWN_EXIT"
    FUNDAMENTAL_EXIT = "FUNDAMENTAL_EXIT"
    COMPOSITE_EXIT = "COMPOSITE_EXIT"


class ExitDecision(StrEnum):
    EXIT = "EXIT"
    HOLD = "HOLD"


class ExitMissingDataPolicy(StrEnum):
    HOLD_POSITION = "hold_position"
    FORCE_EXIT = "force_exit"
    SKIP_EVALUATION = "skip_evaluation"


class CompositeOperator(StrEnum):
    ANY = "ANY"
    ALL = "ALL"
