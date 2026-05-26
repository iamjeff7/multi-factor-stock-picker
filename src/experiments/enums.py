"""Experiment framework enumerations."""

from enum import StrEnum


class ExperimentMode(StrEnum):
    ENTRY = "entry"
    EXIT = "exit"
    ENTRY_AND_EXIT = "entry_and_exit"


class DataPreset(StrEnum):
    DEMO = "demo"
    EXTENDED_DEMO = "extended_demo"
    FULL = "full"


class DateResolution(StrEnum):
    MOST_RECENT_COMPLETE_TRADING_YEAR = "most_recent_complete_trading_year"
    FIXED_RANGE = "fixed_range"


class ExitEvaluationMode(StrEnum):
    FIXED_PERIOD = "fixed_period"
    BEST_WITHIN_FIXED_PERIOD = "best_within_fixed_period"


class EntryEvaluationMode(StrEnum):
    FIXED_PERIOD = "fixed_period"
    BOTTOM_ENTRY = "bottom_entry"


class EntryCadence(StrEnum):
    DAY = "day"
    WEEK = "week"
    TWO_WEEKS = "two_weeks"
    MONTH = "month"


class SegmentRegime(StrEnum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"


class SegmentTertile(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EntryExitEvaluationMode(StrEnum):
    VECTORBT = "vectorbt"
