"""Percentile rank engine tests."""

from decimal import Decimal

import pytest

from core.types import SecurityId
from factors.scoring.config import ScoreRange
from factors.scoring.enums import TieMethod
from factors.scoring.ranking import RankObservation, percentile_rank_scores
from schemas.enums import SignalDirection


def test_spec_example_scores() -> None:
    observations = [
        RankObservation(SecurityId("AAPL"), Decimal("0.40")),
        RankObservation(SecurityId("MSFT"), Decimal("0.25")),
        RankObservation(SecurityId("NVDA"), Decimal("0.10")),
    ]
    results = percentile_rank_scores(
        observations,
        direction=SignalDirection.HIGHER_IS_BETTER,
        tie_method=TieMethod.AVERAGE_RANK,
        score_range=ScoreRange(),
    )

    assert results["AAPL"].factor_rank == Decimal("1")
    assert results["MSFT"].factor_rank == Decimal("2")
    assert results["NVDA"].factor_rank == Decimal("3")
    assert results["AAPL"].factor_score == Decimal("1")
    assert results["MSFT"].factor_score == Decimal("0.5")
    assert results["NVDA"].factor_score == Decimal("0")


def test_lower_is_better_direction() -> None:
    observations = [
        RankObservation(SecurityId("100"), Decimal("10")),
        RankObservation(SecurityId("200"), Decimal("20")),
        RankObservation(SecurityId("300"), Decimal("30")),
    ]
    results = percentile_rank_scores(
        observations,
        direction=SignalDirection.LOWER_IS_BETTER,
        tie_method=TieMethod.AVERAGE_RANK,
        score_range=ScoreRange(),
    )

    assert results["100"].factor_rank == Decimal("1")
    assert results["100"].factor_score == Decimal("1")
    assert results["300"].factor_rank == Decimal("3")
    assert results["300"].factor_score == Decimal("0")


def test_average_rank_for_three_way_tie() -> None:
    observations = [
        RankObservation(SecurityId("100"), Decimal("4")),
        RankObservation(SecurityId("200"), Decimal("3")),
        RankObservation(SecurityId("300"), Decimal("2")),
        RankObservation(SecurityId("400"), Decimal("1")),
        RankObservation(SecurityId("500"), Decimal("0")),
        RankObservation(SecurityId("600"), Decimal("0")),
        RankObservation(SecurityId("700"), Decimal("0")),
    ]

    results = percentile_rank_scores(
        observations,
        direction=SignalDirection.HIGHER_IS_BETTER,
        tie_method=TieMethod.AVERAGE_RANK,
        score_range=ScoreRange(),
    )

    for security_id in ("500", "600", "700"):
        assert results[security_id].factor_rank == Decimal("6")

    assert results["500"].factor_score == results["600"].factor_score == results["700"].factor_score


def test_two_way_tie_uses_fractional_average_rank() -> None:
    observations = [
        RankObservation(SecurityId("100"), Decimal("10")),
        RankObservation(SecurityId("200"), Decimal("10")),
        RankObservation(SecurityId("300"), Decimal("5")),
    ]
    results = percentile_rank_scores(
        observations,
        direction=SignalDirection.HIGHER_IS_BETTER,
        tie_method=TieMethod.AVERAGE_RANK,
        score_range=ScoreRange(),
    )

    assert results["100"].factor_rank == Decimal("1.5")
    assert results["200"].factor_rank == Decimal("1.5")
    assert results["100"].factor_score == results["200"].factor_score
    assert results["300"].factor_rank == Decimal("3")


def test_input_order_does_not_change_output() -> None:
    observations_a = [
        RankObservation(SecurityId("100"), Decimal("0.40")),
        RankObservation(SecurityId("200"), Decimal("0.25")),
        RankObservation(SecurityId("300"), Decimal("0.10")),
    ]
    observations_b = list(reversed(observations_a))

    kwargs = {
        "direction": SignalDirection.HIGHER_IS_BETTER,
        "tie_method": TieMethod.AVERAGE_RANK,
        "score_range": ScoreRange(),
    }
    results_a = percentile_rank_scores(observations_a, **kwargs)
    results_b = percentile_rank_scores(observations_b, **kwargs)
    assert results_a == results_b

@pytest.mark.parametrize("count", [500, 1000])
def test_large_cross_section_monotonicity(count: int) -> None:
    observations = [
        RankObservation(SecurityId(f"{index:04d}"), Decimal(index))
        for index in range(count)
    ]
    results = percentile_rank_scores(
        observations,
        direction=SignalDirection.HIGHER_IS_BETTER,
        tie_method=TieMethod.AVERAGE_RANK,
        score_range=ScoreRange(),
    )

    assert len(results) == count
    assert results["0000"].factor_score == Decimal("0")
    assert results[f"{count - 1:04d}"].factor_score == Decimal("1")

    previous_score = Decimal("-1")
    for index in range(count):
        score = results[f"{index:04d}"].factor_score
        assert score >= previous_score
        previous_score = score
