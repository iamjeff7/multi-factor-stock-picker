"""Build partial entry robustness inputs from factor evaluation outputs."""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from backtest.experiment_config import SingleFactorExperimentConfig
from backtest.factor_evaluation_config import FactorEvaluationSettings
from backtest.robustness_inputs import build_parameter_stability_input
from core.types import SignalId
from data.protocols import DataAccess
from entry_signals.protocols import EntrySignal
from evaluation.robustness.classification import classify_robustness_score
from evaluation.robustness.components import (
    score_factor_decay_resistance,
    score_ic_stability,
    score_out_of_sample_retention,
    score_parameter_stability,
    score_return_stability,
    score_walk_forward_stability_from_ic_series,
)
from evaluation.robustness.config import EntryRobustnessConfig
from evaluation.robustness.normalize import quantize_score
from evaluation.robustness.sample_inputs import (
    build_sample_stability_from_ic_analysis,
    build_sample_stability_from_split,
)
from research.sample_split import SampleSplit
from schemas.factors import FactorScore
from schemas.ic import DailyICResult, ForwardReturn, ICSampleAnalysis, ICSummary
from schemas.robustness import (
    BreadthStabilityInput,
    EntryRobustnessInputs,
    EntryRobustnessResult,
    ICStabilityInput,
    ParameterStabilityInput,
    RankStabilityInput,
    RegimeStabilityInput,
    ReturnStabilityInput,
    SampleStabilityInput,
)

PENDING_ROBUSTNESS_DIMENSIONS = (
    "market_regime_consistency",
    "data_perturbation_resilience",
)

ACTIVE_ROBUSTNESS_WEIGHT_KEYS = (
    "ic_stability",
    "return_stability",
    "walk_forward_stability",
    "out_of_sample_retention",
    "parameter_sensitivity",
    "factor_decay_resistance",
)


def compute_partial_entry_robustness(
    *,
    signal_id: SignalId,
    horizon: int,
    ic_summary: ICSummary | None,
    daily_ic_results: Sequence[DailyICResult],
    forward_returns: Sequence[ForwardReturn],
    split: SampleSplit,
    factor_scores: Sequence[FactorScore] | None = None,
    config: SingleFactorExperimentConfig | None = None,
    data_access: DataAccess | None = None,
    entry_signal: EntrySignal | None = None,
    trading_days: Sequence[date] | None = None,
    settings: FactorEvaluationSettings | None = None,
    ic_analysis: ICSampleAnalysis | None = None,
    scoring_config: EntryRobustnessConfig | None = None,
) -> tuple[EntryRobustnessResult | None, list[str]]:
    """Score available robustness dimensions; regime and perturbation remain pending."""
    _ = factor_scores
    if ic_summary is None or not daily_ic_results:
        return None, list(PENDING_ROBUSTNESS_DIMENSIONS) + ["parameter_sensitivity"]

    config_obj = scoring_config or EntryRobustnessConfig()
    ic_dates = {result.evaluation_date for result in daily_ic_results if result.horizon == horizon}
    return_stability = _build_return_stability_input(
        forward_returns,
        horizon=horizon,
        evaluation_dates=ic_dates,
    )
    if return_stability is None:
        return None, list(PENDING_ROBUSTNESS_DIMENSIONS) + ["parameter_sensitivity"]

    sample_stability = _build_sample_stability_input(
        daily_ic_results=daily_ic_results,
        forward_returns=forward_returns,
        split=split,
        signal_id=signal_id,
        horizon=horizon,
        ic_analysis=ic_analysis,
    )

    pending_dimensions = list(PENDING_ROBUSTNESS_DIMENSIONS)
    parameter_stability = ParameterStabilityInput()
    if (
        config is not None
        and data_access is not None
        and entry_signal is not None
        and trading_days is not None
        and settings is not None
    ):
        built_parameter = build_parameter_stability_input(
            entry_signal=entry_signal,
            config=config,
            data_access=data_access,
            trading_days=trading_days,
            settings=settings,
            horizon=horizon,
        )
        if built_parameter is not None:
            parameter_stability = built_parameter
        else:
            pending_dimensions.append("parameter_sensitivity")
    else:
        pending_dimensions.append("parameter_sensitivity")

    ic_stability = ICStabilityInput.from_ic_summary(ic_summary)
    ic_series = [
        result.ic
        for result in sorted(daily_ic_results, key=lambda row: row.evaluation_date)
        if result.horizon == horizon
    ]
    inputs = EntryRobustnessInputs(
        signal_id=signal_id,
        ic_stability=ic_stability,
        return_stability=return_stability,
        regime_stability=RegimeStabilityInput(),
        parameter_stability=parameter_stability,
        rank_stability=RankStabilityInput(
            top_decile_persistence=Decimal("0"),
            turnover_rate=Decimal("1"),
        ),
        breadth_stability=BreadthStabilityInput(),
        sample_stability=sample_stability,
    )

    ic_stability_score = quantize_score(
        score_ic_stability(inputs.ic_stability, config=config_obj)
    )
    return_stability_score = quantize_score(
        score_return_stability(inputs.return_stability, config=config_obj)
    )
    out_of_sample_retention_score = quantize_score(
        score_out_of_sample_retention(inputs.sample_stability, config=config_obj)
    )
    walk_forward_stability_score = quantize_score(
        score_walk_forward_stability_from_ic_series(ic_series, config=config_obj)
    )
    parameter_sensitivity_score = quantize_score(
        score_parameter_stability(inputs.parameter_stability, config=config_obj)
    )
    factor_decay_resistance_score = quantize_score(score_factor_decay_resistance(ic_series))

    weights = config_obj.component_weights
    component_scores = {
        "ic_stability": ic_stability_score,
        "return_stability": return_stability_score,
        "walk_forward_stability": walk_forward_stability_score,
        "out_of_sample_retention": out_of_sample_retention_score,
        "parameter_sensitivity": parameter_sensitivity_score,
        "factor_decay_resistance": factor_decay_resistance_score,
    }
    active_weight = sum(
        getattr(weights, key)
        for key in ACTIVE_ROBUSTNESS_WEIGHT_KEYS
        if key not in pending_dimensions
    )
    if active_weight <= Decimal("0"):
        return None, pending_dimensions

    overall_robustness_score = quantize_score(
        sum(
            component_scores[key] * getattr(weights, key)
            for key in ACTIVE_ROBUSTNESS_WEIGHT_KEYS
            if key not in pending_dimensions
        )
        / active_weight
    )
    classification = classify_robustness_score(
        overall_robustness_score,
        thresholds=config_obj.classification_thresholds,
    )

    return (
        EntryRobustnessResult(
            signal_id=signal_id,
            ic_stability_score=ic_stability_score,
            return_stability_score=return_stability_score,
            walk_forward_stability_score=walk_forward_stability_score,
            out_of_sample_retention_score=out_of_sample_retention_score,
            market_regime_consistency_score=Decimal("0"),
            parameter_sensitivity_score=parameter_sensitivity_score,
            factor_decay_resistance_score=factor_decay_resistance_score,
            data_perturbation_resilience_score=Decimal("0"),
            overall_robustness_score=overall_robustness_score,
            robustness_classification=classification.value,
        ),
        pending_dimensions,
    )


def resolve_ic_summary(
    *,
    ic_analysis: ICSampleAnalysis | None,
    full_ic_summary: ICSummary | None,
) -> ICSummary | None:
    if ic_analysis is not None:
        if ic_analysis.full_summary is not None:
            return ic_analysis.full_summary
        return ic_analysis.in_sample_summary
    return full_ic_summary


def _build_sample_stability_input(
    *,
    daily_ic_results: Sequence[DailyICResult],
    forward_returns: Sequence[ForwardReturn],
    split: SampleSplit,
    signal_id: SignalId,
    horizon: int,
    ic_analysis: ICSampleAnalysis | None,
) -> SampleStabilityInput:
    if ic_analysis is not None:
        return build_sample_stability_from_ic_analysis(
            ic_analysis,
            forward_returns,
            split=split,
        )
    try:
        return build_sample_stability_from_split(
            daily_ic_results,
            forward_returns,
            split=split,
            signal_id=signal_id,
            horizon=horizon,
        )
    except ValueError:
        return SampleStabilityInput()


def _build_return_stability_input(
    forward_returns: Sequence[ForwardReturn],
    *,
    horizon: int,
    evaluation_dates: set[date],
) -> ReturnStabilityInput | None:
    period_means: list[Decimal] = []
    for evaluation_date in sorted(evaluation_dates):
        values = [
            row.forward_return
            for row in forward_returns
            if row.horizon == horizon and row.evaluation_date == evaluation_date
        ]
        if not values:
            continue
        period_means.append(sum(values, start=Decimal("0")) / Decimal(len(values)))

    if not period_means:
        return None

    mean_forward_return = Decimal(str(statistics.fmean(period_means)))
    median_forward_return = Decimal(str(statistics.median(period_means)))
    return_std = (
        Decimal(str(statistics.pstdev(period_means)))
        if len(period_means) > 1
        else Decimal("0")
    )
    positive_period_ratio = Decimal(
        sum(1 for value in period_means if value > Decimal("0"))
    ) / Decimal(len(period_means))
    return ReturnStabilityInput(
        mean_forward_return=mean_forward_return,
        median_forward_return=median_forward_return,
        return_std=return_std,
        positive_period_ratio=positive_period_ratio,
    )
