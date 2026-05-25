"""Information coefficient interfaces."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal
from typing import Protocol

from core.types import SecurityId, SignalId
from factors.ic.config import ICConfig
from schemas.factors import FactorScore
from schemas.ic import DailyICResult, ForwardReturn, ICSummary


class InformationCoefficientCalculator(Protocol):
    """Computes IC between factor scores and forward returns."""

    def calculate_daily_ic(
        self,
        factor_scores: Sequence[FactorScore],
        forward_returns: Mapping[SecurityId, Decimal] | Sequence[ForwardReturn],
        evaluation_date: date,
        *,
        signal_id: SignalId,
        horizon: int,
        config: ICConfig | None = None,
    ) -> DailyICResult: ...

    def calculate_ic_series(
        self,
        factor_scores: Sequence[FactorScore],
        forward_returns: Sequence[ForwardReturn],
        *,
        signal_id: SignalId,
        horizons: Sequence[int] | None = None,
        config: ICConfig | None = None,
    ) -> Sequence[DailyICResult]: ...

    def summarize(
        self,
        daily_results: Sequence[DailyICResult],
        *,
        signal_id: SignalId,
        horizon: int,
    ) -> ICSummary: ...
