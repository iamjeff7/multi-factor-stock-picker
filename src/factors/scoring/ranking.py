"""Cross-sectional percentile rank scoring."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from core.types import SecurityId
from factors.scoring.config import ScoreRange
from factors.scoring.enums import TieMethod
from schemas.enums import SignalDirection


@dataclass(frozen=True)
class RankObservation:
    security_id: SecurityId
    raw_value: Decimal


@dataclass(frozen=True)
class RankResult:
    factor_rank: Decimal
    factor_score: Decimal


def percentile_rank_scores(
    observations: list[RankObservation],
    *,
    direction: SignalDirection,
    tie_method: TieMethod,
    score_range: ScoreRange,
) -> dict[SecurityId, RankResult]:
    """Rank valid observations and convert ranks to normalized scores."""
    if tie_method != TieMethod.AVERAGE_RANK:
        raise ValueError(f"Unsupported tie method: {tie_method}")

    n = len(observations)
    if n == 0:
        return {}

    sorted_observations = _sort_observations(observations, direction)
    ranks = _average_ranks(sorted_observations)
    scores = _scores_from_ranks(ranks, n=n, score_range=score_range)

    return {
        observation.security_id: RankResult(
            factor_rank=ranks[index],
            factor_score=scores[index],
        )
        for index, observation in enumerate(sorted_observations)
    }


def _sort_observations(
    observations: list[RankObservation],
    direction: SignalDirection,
) -> list[RankObservation]:
    reverse = direction == SignalDirection.HIGHER_IS_BETTER
    return sorted(
        observations,
        key=lambda observation: (observation.raw_value, str(observation.security_id)),
        reverse=reverse,
    )


def _average_ranks(observations: list[RankObservation]) -> list[Decimal]:
    ranks: list[Decimal] = []
    index = 0
    while index < len(observations):
        tie_end = index
        while (
            tie_end + 1 < len(observations)
            and observations[tie_end + 1].raw_value == observations[index].raw_value
        ):
            tie_end += 1

        # Spec §9: average of 1-indexed ordinal ranks in the tie group.
        start_rank = Decimal(index + 1)
        end_rank = Decimal(tie_end + 1)
        average_rank = (start_rank + end_rank) / Decimal("2")
        for _ in range(index, tie_end + 1):
            ranks.append(average_rank)
        index = tie_end + 1
    return ranks


def _scores_from_ranks(
    ranks: list[Decimal],
    *,
    n: int,
    score_range: ScoreRange,
) -> list[Decimal]:
    if n == 1:
        return [score_range.max]

    span = score_range.max - score_range.min
    denominator = Decimal(n - 1)
    count = Decimal(n)
    return [
        score_range.min + span * (count - rank) / denominator
        for rank in ranks
    ]
