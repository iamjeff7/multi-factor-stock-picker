"""Composite ranking tests."""

from decimal import Decimal

from core.types import SecurityId
from factors.combination.ranking import CompositeObservation, average_rank_composite_scores


def test_highest_composite_score_gets_rank_one() -> None:
    observations = [
        CompositeObservation(SecurityId("AAPL"), Decimal("0.82")),
        CompositeObservation(SecurityId("MSFT"), Decimal("0.76")),
        CompositeObservation(SecurityId("NVDA"), Decimal("0.71")),
    ]
    ranks = average_rank_composite_scores(observations)

    assert ranks[SecurityId("AAPL")] == Decimal("1")
    assert ranks[SecurityId("MSFT")] == Decimal("2")
    assert ranks[SecurityId("NVDA")] == Decimal("3")


def test_average_rank_for_tied_composite_scores() -> None:
    observations = [
        CompositeObservation(SecurityId("AAPL"), Decimal("0.80")),
        CompositeObservation(SecurityId("MSFT"), Decimal("0.80")),
        CompositeObservation(SecurityId("NVDA"), Decimal("0.60")),
    ]
    ranks = average_rank_composite_scores(observations)

    assert ranks[SecurityId("AAPL")] == Decimal("1.5")
    assert ranks[SecurityId("MSFT")] == Decimal("1.5")
    assert ranks[SecurityId("NVDA")] == Decimal("3")
