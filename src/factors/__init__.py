"""Factor scoring, combination, and analysis."""

from factors.combination import (
    FactorCombiner,
    FactorCombinationConfig,
    WeightedMeanFactorCombiner,
)
from factors.ic import (
    ForwardReturnCalculator,
    ICConfig,
    InformationCoefficientCalculator,
    SpearmanICCalculator,
)
from factors.scoring import (
    FactorScorer,
    FactorScoringConfig,
    PercentileRankFactorScorer,
)

__all__ = [
    "FactorCombiner",
    "FactorCombinationConfig",
    "FactorScorer",
    "FactorScoringConfig",
    "ForwardReturnCalculator",
    "ICConfig",
    "InformationCoefficientCalculator",
    "PercentileRankFactorScorer",
    "SpearmanICCalculator",
    "WeightedMeanFactorCombiner",
]
