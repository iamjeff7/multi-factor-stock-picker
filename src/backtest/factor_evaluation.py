"""Cross-sectional factor scoring and IC analysis for experiments."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from backtest.calendar import is_rebalance_date
from backtest.entry_robustness import compute_partial_entry_robustness, resolve_ic_summary
from backtest.experiment_config import ExperimentSecurity, SingleFactorExperimentConfig
from backtest.factor_evaluation_config import FactorEvaluationSettings
from core.enums import RebalanceFrequency
from core.exceptions import ValidationError
from core.types import ConfigurationHash, DataVersion, ExperimentId, SignalId, UniverseVersion
from data.protocols import DataAccess
from entry_signals.protocols import EntrySignal
from factors.ic.calculator import SpearmanICCalculator
from factors.ic.config import ICConfig
from factors.ic.forward_returns import ForwardReturnCalculator
from factors.performance.calculator import FactorPerformanceCalculator
from factors.performance.config import FactorPerformanceConfig
from factors.scoring.config import FactorScoringConfig
from factors.scoring.scorer import PercentileRankFactorScorer
from research.sample_split import SampleSplit
from schemas.entry import EntrySignalResult
from schemas.factors import FactorScore
from schemas.ic import DailyICResult, ForwardReturn, ICSampleAnalysis, ICSummary
from schemas.performance import FactorPerformanceSampleAnalysis, FactorPerformanceSummary
from schemas.results import EntrySignalResultRecord, FactorScoreRecord
from schemas.robustness import EntryRobustnessResult
from schemas.universe import UniverseMembership, UniverseMembershipSnapshot, UniverseMetadata


class FactorScoringSummary(BaseModel):
    signal_id: SignalId
    evaluation_dates: int
    total_scores: int
    securities_per_date: int


class FactorEvaluationResult(BaseModel):
    signal_id: SignalId
    horizon: int
    scoring_summary: FactorScoringSummary
    ic_analysis: ICSampleAnalysis | None = None
    full_ic_summary: ICSummary | None = None
    entry_robustness: EntryRobustnessResult | None = None
    robustness_pending_dimensions: list[str] = Field(default_factory=list)
    factor_performance: FactorPerformanceSampleAnalysis | FactorPerformanceSummary | None = None
    daily_ic_count: int = 0
    skipped_dates: int = 0


class CrossSectionalScoreResult(BaseModel):
    raw_results: list[EntrySignalResult]
    factor_scores: list[FactorScore]
    skipped_dates: int


class SingleFactorFactorEvaluator:
    """Runs scoring and IC analysis on experiment rebalance dates."""

    def __init__(
        self,
        *,
        scorer: PercentileRankFactorScorer | None = None,
        forward_return_calculator: ForwardReturnCalculator | None = None,
        ic_calculator: SpearmanICCalculator | None = None,
    ) -> None:
        self._scorer = scorer or PercentileRankFactorScorer()
        self._forward_returns = forward_return_calculator or ForwardReturnCalculator()
        self._ic_calculator = ic_calculator or SpearmanICCalculator()

    def score_cross_section(
        self,
        *,
        config: SingleFactorExperimentConfig,
        data_access: DataAccess,
        entry_signal: EntrySignal,
        trading_days: Sequence[date],
        settings: FactorEvaluationSettings,
    ) -> CrossSectionalScoreResult | None:
        if len(config.securities) < settings.minimum_security_count:
            return None

        scoring_config = FactorScoringConfig(
            minimum_security_count=settings.minimum_security_count,
        )
        scorer = PercentileRankFactorScorer(config=scoring_config)
        signal_id = SignalId(entry_signal.signal_id)
        rebalance_dates = _collect_rebalance_dates(
            list(trading_days),
            config.rebalance_frequency,
        )

        raw_results: list[EntrySignalResult] = []
        factor_scores: list[FactorScore] = []
        skipped_dates = 0

        for evaluation_date in rebalance_dates:
            try:
                date_raw, date_scores, _, _ = self._evaluate_date(
                    evaluation_date=evaluation_date,
                    config=config,
                    data_access=data_access,
                    entry_signal=entry_signal,
                    trading_days=list(trading_days),
                    signal_id=signal_id,
                    scorer=scorer,
                    ic_calculator=SpearmanICCalculator(
                        config=ICConfig(
                            minimum_security_count=settings.minimum_security_count,
                            horizons=list(settings.horizons),
                        )
                    ),
                    settings=settings,
                )
            except ValidationError:
                skipped_dates += 1
                continue

            raw_results.extend(date_raw)
            factor_scores.extend(date_scores)

        if not factor_scores:
            return None

        return CrossSectionalScoreResult(
            raw_results=raw_results,
            factor_scores=factor_scores,
            skipped_dates=skipped_dates,
        )

    def evaluate(
        self,
        *,
        config: SingleFactorExperimentConfig,
        data_access: DataAccess,
        entry_signal: EntrySignal,
        trading_days: Sequence[date],
        split: SampleSplit,
        settings: FactorEvaluationSettings,
        experiment_id: ExperimentId | None = None,
        cross_sectional_scores: CrossSectionalScoreResult | None = None,
    ) -> tuple[
        FactorEvaluationResult | None,
        list[EntrySignalResultRecord],
        list[FactorScoreRecord],
    ]:
        if not settings.enabled:
            return None, [], []

        if cross_sectional_scores is not None:
            raw_results = list(cross_sectional_scores.raw_results)
            factor_scores = list(cross_sectional_scores.factor_scores)
            skipped_dates = cross_sectional_scores.skipped_dates
        else:
            scored = self.score_cross_section(
                config=config,
                data_access=data_access,
                entry_signal=entry_signal,
                trading_days=trading_days,
                settings=settings,
            )
            if scored is None:
                return None, [], []
            raw_results = scored.raw_results
            factor_scores = scored.factor_scores
            skipped_dates = scored.skipped_dates

        if len(config.securities) < settings.minimum_security_count:
            return None, [], []

        ic_config = ICConfig(
            minimum_security_count=settings.minimum_security_count,
            horizons=list(settings.horizons),
        )
        ic_calculator = SpearmanICCalculator(config=ic_config)
        signal_id = SignalId(entry_signal.signal_id)
        rebalance_dates = _collect_rebalance_dates(
            list(trading_days),
            config.rebalance_frequency,
        )

        forward_returns: list[ForwardReturn] = []
        daily_ic_results: list[DailyICResult] = []

        for evaluation_date in rebalance_dates:
            date_scores = [
                row for row in factor_scores if row.evaluation_date == evaluation_date
            ]
            if not date_scores:
                continue

            security_ids = [security.security_id for security in config.securities]
            date_forward_returns: list[ForwardReturn] = []
            for horizon in settings.horizons:
                date_forward_returns.extend(
                    self._forward_returns.calculate_for_universe(
                        security_ids=security_ids,
                        evaluation_date=evaluation_date,
                        horizon=horizon,
                        trading_days=list(trading_days),
                        data_access=data_access,
                    )
                )
            forward_returns.extend(date_forward_returns)

            for horizon in settings.horizons:
                horizon_returns = {
                    row.security_id: row.forward_return
                    for row in date_forward_returns
                    if row.horizon == horizon
                }
                if not horizon_returns:
                    continue
                daily_ic_results.append(
                    ic_calculator.calculate_daily_ic(
                        date_scores,
                        horizon_returns,
                        evaluation_date,
                        signal_id=signal_id,
                        horizon=horizon,
                    )
                )

        if not factor_scores:
            return None, [], []

        evaluation_dates = {row.evaluation_date for row in factor_scores}
        scoring_summary = FactorScoringSummary(
            signal_id=signal_id,
            evaluation_dates=len(evaluation_dates),
            total_scores=len(factor_scores),
            securities_per_date=len(factor_scores) // max(len(evaluation_dates), 1),
        )

        ic_analysis: ICSampleAnalysis | None = None
        full_ic_summary: ICSummary | None = None
        primary_daily_ic = [
            result
            for result in daily_ic_results
            if result.horizon == settings.primary_horizon
        ]
        if primary_daily_ic:
            try:
                ic_analysis = ic_calculator.analyze_by_sample(
                    daily_ic_results,
                    split=split,
                    signal_id=signal_id,
                    horizon=settings.primary_horizon,
                )
            except ValueError:
                full_ic_summary = ic_calculator.summarize(
                    primary_daily_ic,
                    signal_id=signal_id,
                    horizon=settings.primary_horizon,
                )

        ic_summary = resolve_ic_summary(
            ic_analysis=ic_analysis,
            full_ic_summary=full_ic_summary,
        )
        entry_robustness: EntryRobustnessResult | None = None
        pending_dimensions: list[str] = []
        if settings.compute_robustness and ic_summary is not None:
            entry_robustness, pending_dimensions = compute_partial_entry_robustness(
                signal_id=signal_id,
                horizon=settings.primary_horizon,
                ic_summary=ic_summary,
                daily_ic_results=primary_daily_ic,
                forward_returns=forward_returns,
                split=split,
                factor_scores=factor_scores,
                config=config,
                data_access=data_access,
                entry_signal=entry_signal,
                trading_days=trading_days,
                settings=settings,
                ic_analysis=ic_analysis,
            )

        factor_performance = None
        if settings.performance.enabled:
            performance_config = FactorPerformanceConfig(
                quantile_count=settings.performance.quantile_count,
                top_quantile=settings.performance.top_quantile,
                bottom_quantile=settings.performance.bottom_quantile,
            )
            factor_performance = FactorPerformanceCalculator(
                config=performance_config,
            ).analyze(
                factor_scores,
                forward_returns,
                signal_id=signal_id,
                horizon=settings.primary_horizon,
                split=split,
            )

        evaluation_result = FactorEvaluationResult(
            signal_id=signal_id,
            horizon=settings.primary_horizon,
            scoring_summary=scoring_summary,
            ic_analysis=ic_analysis,
            full_ic_summary=full_ic_summary,
            entry_robustness=entry_robustness,
            robustness_pending_dimensions=pending_dimensions,
            factor_performance=factor_performance,
            daily_ic_count=len(primary_daily_ic),
            skipped_dates=skipped_dates,
        )

        entry_records = _to_entry_signal_records(experiment_id, raw_results)
        score_records = _to_factor_score_records(experiment_id, factor_scores)
        return evaluation_result, entry_records, score_records

    def compute_mean_ic(
        self,
        *,
        config: SingleFactorExperimentConfig,
        data_access: DataAccess,
        entry_signal: EntrySignal,
        trading_days: Sequence[date],
        settings: FactorEvaluationSettings,
        horizon: int,
    ) -> Decimal | None:
        scored = self.score_cross_section(
            config=config,
            data_access=data_access,
            entry_signal=entry_signal,
            trading_days=trading_days,
            settings=settings,
        )
        if scored is None:
            return None

        ic_config = ICConfig(
            minimum_security_count=settings.minimum_security_count,
            horizons=[horizon],
        )
        ic_calculator = SpearmanICCalculator(config=ic_config)
        signal_id = SignalId(entry_signal.signal_id)
        rebalance_dates = _collect_rebalance_dates(
            list(trading_days),
            config.rebalance_frequency,
        )

        daily_ic_results: list[DailyICResult] = []
        for evaluation_date in rebalance_dates:
            date_scores = [
                row for row in scored.factor_scores if row.evaluation_date == evaluation_date
            ]
            if not date_scores:
                continue

            security_ids = [security.security_id for security in config.securities]
            date_forward_returns = self._forward_returns.calculate_for_universe(
                security_ids=security_ids,
                evaluation_date=evaluation_date,
                horizon=horizon,
                trading_days=list(trading_days),
                data_access=data_access,
            )
            horizon_returns = {
                row.security_id: row.forward_return
                for row in date_forward_returns
                if row.horizon == horizon
            }
            if not horizon_returns:
                continue
            daily_ic_results.append(
                ic_calculator.calculate_daily_ic(
                    date_scores,
                    horizon_returns,
                    evaluation_date,
                    signal_id=signal_id,
                    horizon=horizon,
                )
            )

        if not daily_ic_results:
            return None

        summary = ic_calculator.summarize(
            daily_ic_results,
            signal_id=signal_id,
            horizon=horizon,
        )
        return summary.mean_ic

    def _evaluate_date(
        self,
        *,
        evaluation_date: date,
        config: SingleFactorExperimentConfig,
        data_access: DataAccess,
        entry_signal: EntrySignal,
        trading_days: list[date],
        signal_id: SignalId,
        scorer: PercentileRankFactorScorer,
        ic_calculator: SpearmanICCalculator,
        settings: FactorEvaluationSettings,
    ) -> tuple[
        list[EntrySignalResult],
        list[FactorScore],
        list[ForwardReturn],
        list[DailyICResult] | None,
    ]:
        universe = _build_universe_snapshot(
            evaluation_date=evaluation_date,
            securities=config.securities,
            data_version=data_access.data_version,
        )
        raw_signals = list(
            entry_signal.calculate(
                evaluation_date,
                universe,
                data_access,
            )
        )
        scores = list(
            scorer.score(
                raw_signals,
                evaluation_date,
                direction=entry_signal.metadata.direction,
            )
        )

        security_ids = [security.security_id for security in config.securities]
        date_forward_returns: list[ForwardReturn] = []
        for horizon in settings.horizons:
            date_forward_returns.extend(
                self._forward_returns.calculate_for_universe(
                    security_ids=security_ids,
                    evaluation_date=evaluation_date,
                    horizon=horizon,
                    trading_days=trading_days,
                    data_access=data_access,
                )
            )

        daily_ic: list[DailyICResult] = []
        for horizon in settings.horizons:
            horizon_returns = {
                row.security_id: row.forward_return
                for row in date_forward_returns
                if row.horizon == horizon
            }
            if not horizon_returns:
                continue
            daily_ic.append(
                ic_calculator.calculate_daily_ic(
                    scores,
                    horizon_returns,
                    evaluation_date,
                    signal_id=signal_id,
                    horizon=horizon,
                )
            )

        return raw_signals, scores, date_forward_returns, daily_ic or None


def _collect_rebalance_dates(
    trading_days: list[date],
    rebalance_frequency: RebalanceFrequency,
) -> list[date]:
    rebalance_dates: list[date] = []
    previous_date: date | None = None
    for current_date in trading_days:
        if is_rebalance_date(current_date, previous_date, rebalance_frequency):
            rebalance_dates.append(current_date)
        previous_date = current_date
    return rebalance_dates


def _build_universe_snapshot(
    *,
    evaluation_date: date,
    securities: Sequence[ExperimentSecurity],
    data_version: DataVersion,
) -> UniverseMembershipSnapshot:
    return UniverseMembershipSnapshot(
        evaluation_date=evaluation_date,
        memberships=[
            UniverseMembership(
                evaluation_date=evaluation_date,
                security_id=security.security_id,
                ticker=security.ticker,
                is_member=True,
            )
            for security in securities
        ],
        metadata=UniverseMetadata(
            universe_version=UniverseVersion("single_factor_cross_section"),
            creation_timestamp=datetime.now(tz=UTC),
            configuration_hash=ConfigurationHash("single_factor"),
            data_version=data_version,
        ),
    )


def _to_entry_signal_records(
    experiment_id: ExperimentId | None,
    raw_results: Sequence[EntrySignalResult],
) -> list[EntrySignalResultRecord]:
    if experiment_id is None:
        return []
    return [
        EntrySignalResultRecord(
            experiment_id=experiment_id,
            evaluation_date=result.evaluation_date,
            security_id=result.security_id,
            ticker=result.ticker,
            signal_id=result.signal_id,
            signal_version=result.signal_version,
            raw_signal_value=result.raw_signal_value,
        )
        for result in raw_results
    ]


def _to_factor_score_records(
    experiment_id: ExperimentId | None,
    factor_scores: Sequence[FactorScore],
) -> list[FactorScoreRecord]:
    if experiment_id is None:
        return []
    return [
        FactorScoreRecord(
            experiment_id=experiment_id,
            evaluation_date=row.evaluation_date,
            security_id=row.security_id,
            ticker=row.ticker,
            signal_id=row.signal_id,
            factor_score=row.factor_score,
            factor_rank=int(row.factor_rank) if row.factor_rank is not None else None,
        )
        for row in factor_scores
    ]
