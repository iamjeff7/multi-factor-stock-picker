"""Cross-sectional composite ranking."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from core.types import SecurityId


@dataclass(frozen=True)
class CompositeObservation:
    security_id: SecurityId
    composite_score: Decimal


def average_rank_composite_scores(
    observations: list[CompositeObservation],
) -> dict[SecurityId, Decimal]:
    """Rank composite scores with average-rank tie handling (highest score = rank 1)."""
    if not observations:
        return {}

    sorted_observations = sorted(
        observations,
        key=lambda observation: (observation.composite_score, str(observation.security_id)),
        reverse=True,
    )
    ranks = _average_ranks(sorted_observations)
    return {
        observation.security_id: ranks[index]
        for index, observation in enumerate(sorted_observations)
    }


def _average_ranks(observations: list[CompositeObservation]) -> list[Decimal]:
    ranks: list[Decimal] = []
    index = 0
    while index < len(observations):
        tie_end = index
        while (
            tie_end + 1 < len(observations)
            and observations[tie_end + 1].composite_score == observations[index].composite_score
        ):
            tie_end += 1

        start_rank = Decimal(index + 1)
        end_rank = Decimal(tie_end + 1)
        average_rank = (start_rank + end_rank) / Decimal("2")
        for _ in range(index, tie_end + 1):
            ranks.append(average_rank)
        index = tie_end + 1
    return ranks
