"""Factor combination."""

from factors.combination.combiner import WeightedMeanFactorCombiner
from factors.combination.config import FactorCombinationConfig
from factors.combination.enums import (
    CombinationMethod,
    MissingFactorPolicy,
    WeightingMethod,
)
from factors.combination.protocols import FactorCombiner
from factors.combination.validator import FactorCombinationValidator

__all__ = [
    "CombinationMethod",
    "FactorCombiner",
    "FactorCombinationConfig",
    "FactorCombinationValidator",
    "MissingFactorPolicy",
    "WeightedMeanFactorCombiner",
    "WeightingMethod",
]
