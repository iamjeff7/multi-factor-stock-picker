"""Factor scoring enumerations."""

from enum import StrEnum


class ScoringMethod(StrEnum):
    PERCENTILE_RANK = "PERCENTILE_RANK"


class TieMethod(StrEnum):
    AVERAGE_RANK = "AVERAGE_RANK"


class ScoringMissingDataPolicy(StrEnum):
    EXCLUDE_SECURITY = "EXCLUDE_SECURITY"
    ASSIGN_LOWEST_SCORE = "ASSIGN_LOWEST_SCORE"
    ASSIGN_NEUTRAL_SCORE = "ASSIGN_NEUTRAL_SCORE"
