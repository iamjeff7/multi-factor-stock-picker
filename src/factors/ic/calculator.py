"""Information coefficient calculator."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal

from core.types import SecurityId, SignalId
from factors.ic.aggregates import summarize_ic_series
from factors.ic.config import ICConfig
from factors.ic.enums import CorrelationMethod
from factors.ic.sample_analysis import analyze_ic_by_sample
from factors.ic.spearman import spearman_correlation
from factors.ic.validator import ICValidator, align_observations
from research.sample_split import SampleSplit
from schemas.factors import FactorScore
from schemas.ic import DailyICResult, ForwardReturn, ICSampleAnalysis, ICSummary


class SpearmanICCalculator:
    """Computes cross-sectional Spearman IC between factor scores and forward returns."""

    def __init__(
        self,
        *,
        config: ICConfig | None = None,
        validator: ICValidator | None = None,
    ) -> None:
        self._config = config or ICConfig()
        self._validator = validator or ICValidator()

    @property
    def config(self) -> ICConfig:
        return self._config

    def calculate_daily_ic(
        self,
        factor_scores: Sequence[FactorScore],
        forward_returns: Mapping[SecurityId, Decimal] | Sequence[ForwardReturn],
        evaluation_date: date,
        *,
        signal_id: SignalId,
        horizon: int,
        config: ICConfig | None = None,
    ) -> DailyICResult:
        ic_config = config or self._config
        if ic_config.correlation_method != CorrelationMethod.SPEARMAN:
            raise ValueError(f"Unsupported correlation method: {ic_config.correlation_method}")

        return_map = _normalize_forward_returns(forward_returns, evaluation_date, horizon)
        self._validator.validate_inputs_or_raise(
            factor_scores,
            return_map,
            evaluation_date,
            signal_id=signal_id,
            config=ic_config,
        )

        scores, returns, security_count = align_observations(factor_scores, return_map)
        ic_value = spearman_correlation(scores, returns)
        result = DailyICResult(
            evaluation_date=evaluation_date,
            signal_id=signal_id,
            horizon=horizon,
            security_count=security_count,
            ic=ic_value,
        )
        self._validator.validate_daily_result_or_raise(result)
        return result

    def calculate_ic_series(
        self,
        factor_scores: Sequence[FactorScore],
        forward_returns: Sequence[ForwardReturn],
        *,
        signal_id: SignalId,
        horizons: Sequence[int] | None = None,
        config: ICConfig | None = None,
    ) -> list[DailyICResult]:
        ic_config = config or self._config
        target_horizons = list(horizons or ic_config.horizons)
        scores_by_date: dict[date, list[FactorScore]] = defaultdict(list)
        for row in factor_scores:
            if row.signal_id == signal_id:
                scores_by_date[row.evaluation_date].append(row)

        results: list[DailyICResult] = []
        for evaluation_date in sorted(scores_by_date):
            horizon_returns = {
                row.security_id: row
                for row in forward_returns
                if row.evaluation_date == evaluation_date
            }
            for horizon in target_horizons:
                return_map = {
                    security_id: row.forward_return
                    for security_id, row in horizon_returns.items()
                    if row.horizon == horizon
                }
                if not return_map:
                    continue
                results.append(
                    self.calculate_daily_ic(
                        scores_by_date[evaluation_date],
                        return_map,
                        evaluation_date,
                        signal_id=signal_id,
                        horizon=horizon,
                        config=ic_config,
                    )
                )
        return results

    def summarize(
        self,
        daily_results: Sequence[DailyICResult],
        *,
        signal_id: SignalId,
        horizon: int,
    ) -> ICSummary:
        filtered = [
            result
            for result in daily_results
            if result.signal_id == signal_id and result.horizon == horizon
        ]
        summary = summarize_ic_series(filtered, signal_id=signal_id, horizon=horizon)
        self._validator.validate_summary_or_raise(summary)
        return summary

    def analyze_by_sample(
        self,
        daily_results: Sequence[DailyICResult],
        *,
        split: SampleSplit,
        signal_id: SignalId,
        horizon: int,
    ) -> ICSampleAnalysis:
        analysis = analyze_ic_by_sample(
            daily_results,
            split=split,
            signal_id=signal_id,
            horizon=horizon,
        )
        for summary in (
            analysis.full_summary,
            analysis.in_sample_summary,
            analysis.out_of_sample_summary,
        ):
            if summary is not None:
                self._validator.validate_summary_or_raise(summary)
        return analysis


def _normalize_forward_returns(
    forward_returns: Mapping[SecurityId, Decimal] | Sequence[ForwardReturn],
    evaluation_date: date,
    horizon: int,
) -> dict[SecurityId, Decimal]:
    if isinstance(forward_returns, Mapping):
        return dict(forward_returns)

    return {
        row.security_id: row.forward_return
        for row in forward_returns
        if row.evaluation_date == evaluation_date and row.horizon == horizon
    }
