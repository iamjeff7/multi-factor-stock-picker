"""Score multiple factors and combine them into composite ranks."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from pydantic import BaseModel, Field

from backtest.experiment_config import SignalConfig, SingleFactorExperimentConfig
from backtest.factor_evaluation import SingleFactorFactorEvaluator
from backtest.factor_evaluation_config import FactorEvaluationSettings
from backtest.multi_factor_experiment_config import MultiFactorExperimentConfig
from core.types import SignalId
from data.protocols import DataAccess
from entry_signals.protocols import EntrySignal
from factors.combination.combiner import WeightedMeanFactorCombiner
from factors.combination.config import FactorCombinationConfig
from schemas.factors import CompositeScore, FactorScore


class FactorCombinationSummary(BaseModel):
    evaluation_dates: int
    total_composite_scores: int
    securities_per_date: int
    factor_signal_ids: list[str] = Field(default_factory=list)
    skipped_dates: int = 0


class MultiFactorCrossSectionResult(BaseModel):
    factor_scores: list[FactorScore] = Field(default_factory=list)
    composite_scores: list[CompositeScore] = Field(default_factory=list)
    skipped_dates: int = 0


class MultiFactorCombinationResult(BaseModel):
    summary: FactorCombinationSummary
    cross_section: MultiFactorCrossSectionResult


def score_and_combine_multi_factor(
    *,
    config: MultiFactorExperimentConfig,
    data_access: DataAccess,
    entry_signals: Sequence[EntrySignal],
    trading_days: Sequence[date],
    settings: FactorEvaluationSettings,
    combiner: WeightedMeanFactorCombiner | None = None,
) -> MultiFactorCrossSectionResult | None:
    """Score each entry signal cross-sectionally and combine into composite ranks."""
    if len(entry_signals) != len(config.entry_signals):
        raise ValueError("entry_signals must match config.entry_signals")

    if len(config.securities) < settings.minimum_security_count:
        return None

    evaluator = SingleFactorFactorEvaluator()
    all_factor_scores: list[FactorScore] = []
    skipped_dates = 0

    for signal_config, entry_signal in zip(config.entry_signals, entry_signals, strict=True):
        single_config = _as_single_factor_config(config, signal_config)
        scored = evaluator.score_cross_section(
            config=single_config,
            data_access=data_access,
            entry_signal=entry_signal,
            trading_days=trading_days,
            settings=settings,
        )
        if scored is None:
            return None
        all_factor_scores.extend(scored.factor_scores)
        skipped_dates = max(skipped_dates, scored.skipped_dates)

    combination = combiner or WeightedMeanFactorCombiner(config=config.factor_combination)
    composite_scores = _combine_by_date(
        all_factor_scores,
        combination_config=config.factor_combination,
        combiner=combination,
    )
    if not composite_scores:
        return None

    return MultiFactorCrossSectionResult(
        factor_scores=all_factor_scores,
        composite_scores=composite_scores,
        skipped_dates=skipped_dates,
    )


def build_combination_result(
    cross_section: MultiFactorCrossSectionResult,
    *,
    factor_signal_ids: Sequence[SignalId],
) -> MultiFactorCombinationResult:
    dates = {row.evaluation_date for row in cross_section.composite_scores}
    securities_per_date = 0
    if dates:
        first_date = next(iter(dates))
        securities_per_date = sum(
            1 for row in cross_section.composite_scores if row.evaluation_date == first_date
        )

    return MultiFactorCombinationResult(
        summary=FactorCombinationSummary(
            evaluation_dates=len(dates),
            total_composite_scores=len(cross_section.composite_scores),
            securities_per_date=securities_per_date,
            factor_signal_ids=[str(signal_id) for signal_id in factor_signal_ids],
            skipped_dates=cross_section.skipped_dates,
        ),
        cross_section=cross_section,
    )


def _as_single_factor_config(
    config: MultiFactorExperimentConfig,
    entry_signal: SignalConfig,
) -> SingleFactorExperimentConfig:
    return SingleFactorExperimentConfig(
        experiment_name=config.experiment_name,
        start_date=config.start_date,
        end_date=config.end_date,
        initial_capital=config.initial_capital,
        execution_price=config.execution_price,
        commission_pct=config.commission_pct,
        commission_per_trade=config.commission_per_trade,
        slippage_pct=config.slippage_pct,
        rebalance_frequency=config.rebalance_frequency,
        portfolio_mode=config.portfolio_mode,
        position_size_method=config.position_size_method,
        fixed_dollar_amount=config.fixed_dollar_amount,
        securities=list(config.securities),
        universe=config.universe,
        entry_signal=entry_signal,
        exit_signal=config.exit_signal,
        research=config.research,
        factor_evaluation=config.factor_evaluation,
        top_n=config.top_n,
    )


def _combine_by_date(
    factor_scores: Sequence[FactorScore],
    *,
    combination_config: FactorCombinationConfig,
    combiner: WeightedMeanFactorCombiner,
) -> list[CompositeScore]:
    by_date: dict[date, list[FactorScore]] = {}
    for row in factor_scores:
        by_date.setdefault(row.evaluation_date, []).append(row)

    composite_scores: list[CompositeScore] = []
    for evaluation_date in sorted(by_date):
        date_scores = combiner.combine(
            by_date[evaluation_date],
            evaluation_date,
            config=combination_config,
        )
        composite_scores.extend(date_scores)

    return composite_scores
