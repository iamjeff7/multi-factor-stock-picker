"""Factor ranking with percentile normalization and weighted composite scores."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from experiments.scoring.weights import (
    DEFAULT_ENTRY_METRIC_WEIGHTS,
    ENTRY_HIGHER_IS_BETTER,
)
from experiments.segments import SegmentLabels


@dataclass(frozen=True)
class FactorVariantRef:
    signal_id: str
    variant_id: str
    exit_horizon_months: int | None = None
    entry_cadence: str | None = None


@dataclass
class FactorScoreBreakdown:
    raw_metrics: dict[str, Decimal | None]
    percentile_ranks: dict[str, Decimal]
    metric_weights: dict[str, Decimal]
    weighted_metric_score: Decimal
    robustness_score: Decimal | None
    final_score: Decimal
    rank: int | None = None
    evaluation_summary: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        payload = {
            "raw_metrics": {
                key: str(value) if value is not None else None
                for key, value in self.raw_metrics.items()
            },
            "percentile_ranks": {key: str(value) for key, value in self.percentile_ranks.items()},
            "metric_weights": {key: str(value) for key, value in self.metric_weights.items()},
            "weighted_metric_score": str(self.weighted_metric_score),
            "robustness_score": (
                str(self.robustness_score) if self.robustness_score is not None else None
            ),
            "final_score": str(self.final_score),
            "rank": self.rank,
        }
        if self.evaluation_summary is not None:
            payload["evaluation_summary"] = self.evaluation_summary
        return payload


@dataclass
class RankedFactor:
    factor: FactorVariantRef
    segment: SegmentLabels
    qualified: bool
    selection_weight: Decimal
    score_breakdown: FactorScoreBreakdown


DEFAULT_QUALIFYING_PERCENTILE = 95
DEFAULT_MIN_QUALIFYING_FACTORS = 1


def percentile_rank(value: Decimal, values: list[Decimal], *, higher_is_better: bool) -> Decimal:
    if not values:
        return Decimal("0.5")
    sorted_values = sorted(values, key=float, reverse=not higher_is_better)
    numeric = float(value)
    if higher_is_better:
        below = sum(1 for item in sorted_values if float(item) < numeric)
    else:
        below = sum(1 for item in sorted_values if float(item) > numeric)
    return Decimal(str(below / len(sorted_values)))


def compute_factor_score(
    metrics: dict[str, Decimal | None],
    *,
    metric_weights: dict[str, Decimal],
    higher_is_better: dict[str, bool],
    peer_metrics: list[dict[str, Decimal | None]],
    evaluation_summary: dict[str, object] | None = None,
) -> FactorScoreBreakdown:
    weights = metric_weights
    raw = dict(metrics)
    robustness_score = raw.get("robustness_score")

    peer_raw = [dict(peer) for peer in peer_metrics]
    percentile_ranks: dict[str, Decimal] = {}
    for metric_name in weights:
        values = [
            row[metric_name]
            for row in peer_raw + [raw]
            if row.get(metric_name) is not None
        ]
        current = raw.get(metric_name)
        direction = higher_is_better.get(metric_name, True)
        if current is None or not values:
            percentile_ranks[metric_name] = Decimal("0.5")
            continue
        percentile_ranks[metric_name] = percentile_rank(
            current,
            values,
            higher_is_better=direction,
        )

    weighted_metric_score = sum(
        (weights[name] * percentile_ranks[name] for name in weights),
        Decimal("0"),
    )

    return FactorScoreBreakdown(
        raw_metrics=raw,
        percentile_ranks=percentile_ranks,
        metric_weights=weights,
        weighted_metric_score=weighted_metric_score,
        robustness_score=robustness_score,
        final_score=weighted_metric_score,
        evaluation_summary=evaluation_summary,
    )


RankCandidate = tuple[
    FactorVariantRef,
    dict[str, Decimal | None],
    dict[str, object] | None,
]


def rank_factors_in_segment(
    candidates: list[RankCandidate],
    segment: SegmentLabels,
    *,
    qualifying_percentile: int = DEFAULT_QUALIFYING_PERCENTILE,
    min_qualifying_factors: int = DEFAULT_MIN_QUALIFYING_FACTORS,
    metric_weights: dict[str, Decimal] | None = None,
    higher_is_better: dict[str, bool] | None = None,
) -> tuple[Decimal, list[RankedFactor]]:
    weights = metric_weights or DEFAULT_ENTRY_METRIC_WEIGHTS
    direction = higher_is_better or ENTRY_HIGHER_IS_BETTER
    peer_metrics = [metrics for _, metrics, _ in candidates]
    breakdowns: list[tuple[FactorVariantRef, FactorScoreBreakdown]] = []
    for factor, metrics, evaluation_summary in candidates:
        breakdown = compute_factor_score(
            metrics,
            metric_weights=weights,
            higher_is_better=direction,
            peer_metrics=peer_metrics,
            evaluation_summary=evaluation_summary,
        )
        breakdowns.append((factor, breakdown))

    scores = [breakdown.final_score for _, breakdown in breakdowns]
    threshold = _percentile_threshold(scores, qualifying_percentile)

    qualifying_scores = [
        breakdown.final_score
        for _, breakdown in breakdowns
        if breakdown.final_score >= threshold
    ]

    if len(qualifying_scores) < min_qualifying_factors and breakdowns:
        _, best_breakdown = max(breakdowns, key=lambda row: row[1].final_score)
        threshold = best_breakdown.final_score
        qualifying_scores = [best_breakdown.final_score]

    score_total = sum(qualifying_scores, Decimal("0"))
    ranked: list[RankedFactor] = []
    for factor, breakdown in sorted(breakdowns, key=lambda row: row[1].final_score, reverse=True):
        qualified = breakdown.final_score >= threshold or (
            len(qualifying_scores) < min_qualifying_factors
            and breakdown.final_score == threshold
        )
        if len(qualifying_scores) < min_qualifying_factors and breakdowns:
            qualified = breakdown.final_score == threshold
        weight = (
            breakdown.final_score / score_total
            if qualified and score_total > Decimal("0")
            else Decimal("0")
        )
        ranked.append(
            RankedFactor(
                factor=factor,
                segment=segment,
                qualified=qualified,
                selection_weight=weight,
                score_breakdown=breakdown,
            )
        )
    _assign_ranks(ranked)
    return threshold, ranked


def _percentile_threshold(scores: list[Decimal], percentile: int) -> Decimal:
    if not scores:
        return Decimal("0")
    ordered = sorted(scores, key=float)
    index = min(len(ordered) - 1, max(0, int(round((percentile / 100) * (len(ordered) - 1)))))
    return ordered[index]


def _assign_ranks(ranked: list[RankedFactor]) -> None:
    rank = 1
    for item in sorted(
        [row for row in ranked if row.qualified],
        key=lambda row: row.score_breakdown.final_score,
        reverse=True,
    ):
        item.score_breakdown.rank = rank
        rank += 1
