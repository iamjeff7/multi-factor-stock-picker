"""Position sizing and portfolio selection interfaces."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Protocol

from schemas.factors import CompositeScore
from schemas.portfolio import PortfolioSelection


class PortfolioConstructor(Protocol):
    """Selects securities and target weights from composite scores."""

    def select(
        self,
        composite_scores: Sequence[CompositeScore],
        evaluation_date: date,
    ) -> Sequence[PortfolioSelection]: ...
