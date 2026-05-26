"""Build partial entry robustness inputs from factor evaluation outputs."""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from core.types import SignalId
from evaluation.robustness.classification import classify_robustness_score
from evaluation.robustness.components import (
    score_ic_stability,
    score_return_stability,
    score_sample_stability,
)
from evaluation.robustness.config import EntryRobustnessConfig
from evaluation.robustness.normalize import quantize_score
from evaluation.robustness.sample_inputs import (
    build_sample_stability_from_ic_analysis,
    build_sample_stability_from_split,
)
from research.sample_split import SampleSplit
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
    "regime_stability",
    "parameter_stability",
    "rank_stability",
    "breadth_stability",
)

PARTIAL_ROBUSTNESS_WEIGHT_KEYS = (
    "ic_stability",
    "return_stability",
    "sample_stability",
)


def compute_partial_entry_robustness(
    *,
    signal_id: SignalId,
    horizon: int,
    ic_summary: ICSummary | None,
    daily_ic_results: Sequence[DailyICResult],
    forward_returns: Sequence[ForwardReturn],
    split: SampleSplit,
    ic_analysis: ICSampleAnalysis | None = None,
    config: EntryRobustnessConfig | None = None,
) -> tuple[EntryRobustnessResult | None, list[str]]:
    """Score IC, return, and sample stability; leave other dimensions pending."""
    if ic_summary is None or not daily_ic_results:
        return None, list(PENDING_ROBUSTNESS_DIMENSIONS)

    scoring_config = config or EntryRobustnessConfig()
    ic_dates = {result.evaluation_date for result in daily_ic_results if result.horizon == horizon}
    return_stability = _build_return_stability_input(
        forward_returns,
        horizon=horizon,
        evaluation_dates=ic_dates,
    )
    if return_stability is None:
        return None, list(PENDING_ROBUSTNESS_DIMENSIONS)

    sample_stability = _build_sample_stability_input(
        daily_ic_results=daily_ic_results,
        forward_returns=forward_returns,
        split=split,
        signal_id=signal_id,
        horizon=horizon,
        ic_analysis=ic_analysis,
    )

    ic_stability = ICStabilityInput.from_ic_summary(ic_summary)
    inputs = EntryRobustnessInputs(
        signal_id=signal_id,
        ic_stability=ic_stability,
        return_stability=return_stability,
        regime_stability=RegimeStabilityInput(),
        parameter_stability=ParameterStabilityInput(),
        rank_stability=RankStabilityInput(
            top_decile_persistence=Decimal("0"),
            turnover_rate=Decimal("1"),
        ),
        breadth_stability=BreadthStabilityInput(),
        sample_stability=sample_stability,
    )

    ic_stability_score = quantize_score(
        score_ic_stability(inputs.ic_stability, config=scoring_config)
    )
    return_stability_score = quantize_score(
        score_return_stability(inputs.return_stability, config=scoring_config)
    )
    sample_stability_score = quantize_score(
        score_sample_stability(inputs.sample_stability, config=scoring_config)
    )

    weights = scoring_config.component_weights
    partial_weight = (
        weights.ic_stability + weights.return_stability + weights.sample_stability
    )
    overall_robustness_score = quantize_score(
        (
            ic_stability_score * weights.ic_stability
            + return_stability_score * weights.return_stability
            + sample_stability_score * weights.sample_stability
        )
        / partial_weight
    )
    classification = classify_robustness_score(
        overall_robustness_score,
        thresholds=scoring_config.classification_thresholds,
    )

    return (
        EntryRobustnessResult(
            signal_id=signal_id,
            ic_stability_score=ic_stability_score,
            return_stability_score=return_stability_score,
            regime_stability_score=Decimal("0"),
            parameter_stability_score=Decimal("0"),
            rank_stability_score=Decimal("0"),
            breadth_stability_score=Decimal("0"),
            sample_stability_score=sample_stability_score,
            overall_robustness_score=overall_robustness_score,
            robustness_classification=classification.value,
        ),
        list(PENDING_ROBUSTNESS_DIMENSIONS),
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
