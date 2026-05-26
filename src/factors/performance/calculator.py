"""Factor performance calculator."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from core.types import SecurityId, SignalId
from factors.performance.aggregates import analyze_performance_by_sample, summarize_performance
from factors.performance.config import FactorPerformanceConfig
from factors.performance.quantiles import compute_quantile_returns, compute_spread_and_long_short
from factors.performance.validator import FactorPerformanceValidator
from research.sample_split import SampleSplit
from schemas.factors import FactorScore
from schemas.ic import ForwardReturn
from schemas.performance import (
    FactorPerformanceSampleAnalysis,
    FactorPerformanceSummary,
    LongShortResult,
    QuantileReturnResult,
    SpreadResult,
)


class FactorPerformanceCalculator:
    """Computes quantile spreads and long-short performance from factor scores."""

    def __init__(
        self,
        *,
        config: FactorPerformanceConfig | None = None,
        validator: FactorPerformanceValidator | None = None,
    ) -> None:
        self._config = config or FactorPerformanceConfig()
        self._validator = validator or FactorPerformanceValidator()

    @property
    def config(self) -> FactorPerformanceConfig:
        return self._config

    def analyze(
        self,
        factor_scores: Sequence[FactorScore],
        forward_returns: Sequence[ForwardReturn],
        *,
        signal_id: SignalId,
        horizon: int,
        split: SampleSplit,
    ) -> FactorPerformanceSampleAnalysis | FactorPerformanceSummary | None:
        self._validator.validate_inputs_or_raise(
            factor_scores,
            forward_returns,
            horizon=horizon,
            config=self._config,
        )

        quantile_returns, spreads, long_shorts = self._compute_period_results(
            factor_scores=factor_scores,
            forward_returns=forward_returns,
            signal_id=signal_id,
            horizon=horizon,
        )
        if not spreads:
            return None

        try:
            return analyze_performance_by_sample(
                signal_id=signal_id,
                horizon=horizon,
                quantile_returns=quantile_returns,
                spreads=spreads,
                long_shorts=long_shorts,
                split=split,
                config=self._config,
            )
        except ValueError:
            return summarize_performance(
                signal_id=signal_id,
                horizon=horizon,
                quantile_returns=quantile_returns,
                spreads=spreads,
                long_shorts=long_shorts,
                config=self._config,
            )

    def _compute_period_results(
        self,
        *,
        factor_scores: Sequence[FactorScore],
        forward_returns: Sequence[ForwardReturn],
        signal_id: SignalId,
        horizon: int,
    ) -> tuple[list[QuantileReturnResult], list[SpreadResult], list[LongShortResult]]:
        returns_by_date: dict[date, dict[SecurityId, Decimal]] = {}
        for forward_return in forward_returns:
            if forward_return.horizon != horizon:
                continue
            returns_by_date.setdefault(forward_return.evaluation_date, {})[
                forward_return.security_id
            ] = forward_return.forward_return

        scores_by_date: dict[date, list[FactorScore]] = {}
        for score in factor_scores:
            scores_by_date.setdefault(score.evaluation_date, []).append(score)

        quantile_returns: list[QuantileReturnResult] = []
        spreads: list[SpreadResult] = []
        long_shorts: list[LongShortResult] = []

        for evaluation_date in sorted(scores_by_date):
            date_scores = scores_by_date[evaluation_date]
            horizon_returns = returns_by_date.get(evaluation_date)
            if not horizon_returns:
                continue

            date_quantiles = compute_quantile_returns(
                evaluation_date=evaluation_date,
                signal_id=signal_id,
                horizon=horizon,
                scores=date_scores,
                forward_returns=horizon_returns,
                config=self._config,
            )
            spread, long_short = compute_spread_and_long_short(
                date_quantiles,
                config=self._config,
            )
            quantile_returns.extend(date_quantiles)
            if spread is not None and long_short is not None:
                spreads.append(spread)
                long_shorts.append(long_short)

        return quantile_returns, spreads, long_shorts
