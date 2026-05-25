"""Factor combination interfaces."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Protocol

from factors.combination.config import FactorCombinationConfig
from schemas.factors import CompositeScore, FactorScore


class FactorCombiner(Protocol):
    """Combines factor scores into composite scores."""

    def combine(
        self,
        factor_scores: Sequence[FactorScore],
        evaluation_date: date,
        *,
        config: FactorCombinationConfig | None = None,
    ) -> Sequence[CompositeScore]: ...
