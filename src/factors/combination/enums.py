"""Factor combination enumerations."""

from enum import StrEnum


class CombinationMethod(StrEnum):
    WEIGHTED_MEAN = "WEIGHTED_MEAN"


class WeightingMethod(StrEnum):
    EQUAL_WEIGHT = "EQUAL_WEIGHT"
    CUSTOM_WEIGHT = "CUSTOM_WEIGHT"


class MissingFactorPolicy(StrEnum):
    EXCLUDE_SECURITY = "EXCLUDE_SECURITY"
    IGNORE_MISSING_FACTOR = "IGNORE_MISSING_FACTOR"
    ASSIGN_NEUTRAL_SCORE = "ASSIGN_NEUTRAL_SCORE"
