"""Missing-data and tie handling tests."""

from datetime import date
from decimal import Decimal

from tests.factors.scoring.conftest import make_cross_section

from factors.scoring.config import FactorScoringConfig
from factors.scoring.scorer import PercentileRankFactorScorer
from schemas.enums import SignalDirection


def test_tied_values_receive_equal_scores() -> None:
    config = FactorScoringConfig(minimum_security_count=3)
    scorer = PercentileRankFactorScorer(config=config)
    raw_signals = make_cross_section(
        {
            "AAPL": Decimal("0.40"),
            "MSFT": Decimal("0.40"),
            "NVDA": Decimal("0.10"),
        }
    )

    scores = scorer.score(
        raw_signals,
        date(2020, 1, 31),
        direction=SignalDirection.HIGHER_IS_BETTER,
    )
    by_ticker = {row.ticker: row for row in scores}

    assert by_ticker["AAPL"].factor_rank == Decimal("1.5")
    assert by_ticker["MSFT"].factor_rank == Decimal("1.5")
    assert by_ticker["AAPL"].factor_score == by_ticker["MSFT"].factor_score
    assert by_ticker["NVDA"].factor_rank == Decimal("3")
