"""Build rank-stability inputs from cross-sectional factor scores."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from core.types import SecurityId
from factors.ic.spearman import spearman_correlation
from schemas.factors import FactorScore
from schemas.robustness import RankStabilityInput


def build_rank_stability_from_factor_scores(
    factor_scores: Sequence[FactorScore],
    *,
    top_fraction: Decimal = Decimal("0.10"),
) -> RankStabilityInput | None:
    """Derive rank correlation, top-group persistence, and turnover from factor scores."""
    by_date: dict[date, list[FactorScore]] = defaultdict(list)
    for row in factor_scores:
        by_date[row.evaluation_date].append(row)

    dates = sorted(by_date)
    if len(dates) < 2:
        return None

    rank_correlations: list[Decimal] = []
    persistence_values: list[Decimal] = []

    for previous_date, current_date in zip(dates, dates[1:], strict=False):
        previous_ranks = _ordinal_ranks(by_date[previous_date])
        current_ranks = _ordinal_ranks(by_date[current_date])
        common = sorted(set(previous_ranks) & set(current_ranks), key=str)
        if len(common) >= 2:
            previous_series = [previous_ranks[security_id] for security_id in common]
            current_series = [current_ranks[security_id] for security_id in common]
            rank_correlations.append(spearman_correlation(previous_series, current_series))

        previous_top = _top_group(by_date[previous_date], top_fraction)
        current_top = _top_group(by_date[current_date], top_fraction)
        if previous_top:
            overlap = Decimal(len(previous_top & current_top)) / Decimal(len(previous_top))
            persistence_values.append(overlap)

    top_decile_persistence = (
        sum(persistence_values, start=Decimal("0")) / Decimal(len(persistence_values))
        if persistence_values
        else Decimal("0")
    )
    turnover_rate = Decimal("1") - top_decile_persistence

    return RankStabilityInput(
        rank_correlations=rank_correlations,
        top_decile_persistence=top_decile_persistence,
        turnover_rate=turnover_rate,
    )


def _ordinal_ranks(scores: Sequence[FactorScore]) -> dict[SecurityId, Decimal]:
    ordered = sorted(scores, key=lambda row: (row.factor_score, str(row.security_id)), reverse=True)
    return {row.security_id: Decimal(index + 1) for index, row in enumerate(ordered)}


def _top_group(scores: Sequence[FactorScore], top_fraction: Decimal) -> set[SecurityId]:
    ordered = sorted(scores, key=lambda row: (row.factor_score, str(row.security_id)), reverse=True)
    group_size = max(1, math.ceil(len(ordered) * float(top_fraction)))
    return {row.security_id for row in ordered[:group_size]}
