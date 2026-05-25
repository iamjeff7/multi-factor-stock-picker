"""PercentileRankFactorScorer integration tests."""

from datetime import date
from decimal import Decimal

import pytest

from core.exceptions import ValidationError
from core.types import SecurityId, SignalId, Ticker
from factors.scoring.config import FactorScoringConfig
from factors.scoring.enums import ScoringMissingDataPolicy
from factors.scoring.scorer import PercentileRankFactorScorer
from schemas.entry import EntrySignalResult
from schemas.enums import SignalDirection
from tests.factors.scoring.conftest import (
    make_cross_section,
    make_entry_signal_result,
    make_minimum_cross_section,
)


@pytest.fixture
def small_sample_config() -> FactorScoringConfig:
    return FactorScoringConfig(minimum_security_count=3)


def test_spec_example_end_to_end(small_sample_config: FactorScoringConfig) -> None:
    scorer = PercentileRankFactorScorer(config=small_sample_config)
    raw_signals = make_cross_section(
        {
            "AAPL": Decimal("0.40"),
            "MSFT": Decimal("0.25"),
            "NVDA": Decimal("0.10"),
        }
    )

    scores = scorer.score(
        raw_signals,
        date(2020, 1, 31),
        direction=SignalDirection.HIGHER_IS_BETTER,
    )
    by_ticker = {row.ticker: row for row in scores}

    assert by_ticker["AAPL"].factor_rank == Decimal("1")
    assert by_ticker["MSFT"].factor_rank == Decimal("2")
    assert by_ticker["NVDA"].factor_rank == Decimal("3")
    assert by_ticker["AAPL"].factor_score == Decimal("1")
    assert by_ticker["MSFT"].factor_score == Decimal("0.5")
    assert by_ticker["NVDA"].factor_score == Decimal("0")


def test_missing_values_excluded_by_default() -> None:
    config = FactorScoringConfig(minimum_security_count=2)
    scorer = PercentileRankFactorScorer(config=config)
    raw_signals = make_cross_section(
        {
            "AAPL": Decimal("0.40"),
            "MSFT": None,
            "NVDA": Decimal("0.10"),
        }
    )

    scores = scorer.score(
        raw_signals,
        date(2020, 1, 31),
        direction=SignalDirection.HIGHER_IS_BETTER,
    )

    assert len(scores) == 2
    assert {row.ticker for row in scores} == {"AAPL", "NVDA"}


def test_assign_lowest_score_policy() -> None:
    config = FactorScoringConfig(
        minimum_security_count=2,
        missing_data_policy=ScoringMissingDataPolicy.ASSIGN_LOWEST_SCORE,
    )
    scorer = PercentileRankFactorScorer(config=config)
    raw_signals = make_cross_section(
        {
            "AAPL": Decimal("0.40"),
            "MSFT": None,
            "NVDA": Decimal("0.10"),
        }
    )

    scores = scorer.score(
        raw_signals,
        date(2020, 1, 31),
        direction=SignalDirection.HIGHER_IS_BETTER,
    )
    missing = next(row for row in scores if row.ticker == "MSFT")

    assert missing.factor_rank is None
    assert missing.factor_score == Decimal("0")


def test_assign_neutral_score_policy() -> None:
    config = FactorScoringConfig(
        minimum_security_count=2,
        missing_data_policy=ScoringMissingDataPolicy.ASSIGN_NEUTRAL_SCORE,
    )
    scorer = PercentileRankFactorScorer(config=config)
    raw_signals = make_cross_section(
        {
            "AAPL": Decimal("0.40"),
            "MSFT": None,
            "NVDA": Decimal("0.10"),
        }
    )

    scores = scorer.score(
        raw_signals,
        date(2020, 1, 31),
        direction=SignalDirection.HIGHER_IS_BETTER,
    )
    missing = next(row for row in scores if row.ticker == "MSFT")

    assert missing.factor_rank is None
    assert missing.factor_score == Decimal("0.5")


def test_non_finite_values_use_missing_policy() -> None:
    config = FactorScoringConfig(minimum_security_count=2)
    scorer = PercentileRankFactorScorer(config=config)
    raw_signals = [
        make_entry_signal_result(
            security_id="AAPL",
            ticker="AAPL",
            raw_value=Decimal("0.40"),
        ),
        EntrySignalResult.model_construct(
            evaluation_date=date(2020, 1, 31),
            security_id=SecurityId("MSFT"),
            ticker=Ticker("MSFT"),
            signal_id=SignalId("momentum_12m"),
            signal_version="1.0",
            raw_signal_value=Decimal("NaN"),
        ),
        make_entry_signal_result(
            security_id="NVDA",
            ticker="NVDA",
            raw_value=Decimal("0.10"),
        ),
    ]

    scores = scorer.score(
        raw_signals,
        date(2020, 1, 31),
        direction=SignalDirection.HIGHER_IS_BETTER,
    )

    assert len(scores) == 2


def test_default_minimum_sample_halts_execution() -> None:
    scorer = PercentileRankFactorScorer()
    raw_signals = make_minimum_cross_section(29)

    with pytest.raises(ValidationError, match="Valid observation count 29"):
        scorer.score(
            raw_signals,
            date(2020, 1, 31),
            direction=SignalDirection.HIGHER_IS_BETTER,
        )


def test_large_cross_section_with_default_minimum() -> None:
    scorer = PercentileRankFactorScorer()
    raw_signals = make_minimum_cross_section(30)

    scores = scorer.score(
        raw_signals,
        date(2020, 1, 31),
        direction=SignalDirection.HIGHER_IS_BETTER,
    )

    assert len(scores) == 30
    assert scores[0].factor_score == Decimal("0")
    assert scores[-1].factor_score == Decimal("1")


def test_reproducible_output_when_input_order_changes(
    small_sample_config: FactorScoringConfig,
) -> None:
    scorer = PercentileRankFactorScorer(config=small_sample_config)
    values = {
        "AAPL": Decimal("0.40"),
        "MSFT": Decimal("0.25"),
        "NVDA": Decimal("0.10"),
    }
    first = scorer.score(
        make_cross_section(values),
        date(2020, 1, 31),
        direction=SignalDirection.HIGHER_IS_BETTER,
    )
    second = scorer.score(
        list(reversed(make_cross_section(values))),
        date(2020, 1, 31),
        direction=SignalDirection.HIGHER_IS_BETTER,
    )

    assert first == second
