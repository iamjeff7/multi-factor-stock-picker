"""Factor scoring interfaces."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Protocol

from factors.scoring.config import FactorScoringConfig
from schemas.entry import EntrySignalResult
from schemas.enums import SignalDirection
from schemas.factors import FactorScore


class FactorScorer(Protocol):
    """Normalizes raw entry signal values into factor scores."""

    def score(
        self,
        raw_signals: Sequence[EntrySignalResult],
        evaluation_date: date,
        *,
        direction: SignalDirection,
        config: FactorScoringConfig | None = None,
    ) -> Sequence[FactorScore]: ...
