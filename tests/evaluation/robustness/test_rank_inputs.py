"""Rank stability input builder tests."""

from datetime import date
from decimal import Decimal

from core.types import SecurityId, SignalId, Ticker
from evaluation.robustness.rank_inputs import build_rank_stability_from_factor_scores
from schemas.factors import FactorScore


def _score(
    security_id: str,
    evaluation_date: date,
    factor_score: str,
) -> FactorScore:
    return FactorScore(
        evaluation_date=evaluation_date,
        security_id=SecurityId(security_id),
        ticker=Ticker(security_id.removeprefix("SEC_")),
        signal_id=SignalId("momentum_12_1"),
        factor_score=Decimal(factor_score),
    )


def test_build_rank_stability_computes_persistence_for_stable_rankings() -> None:
    date_one = date(2020, 1, 31)
    date_two = date(2020, 2, 29)
    factor_scores = [
        _score("SEC_A", date_one, "0.9"),
        _score("SEC_B", date_one, "0.5"),
        _score("SEC_C", date_one, "0.1"),
        _score("SEC_A", date_two, "0.8"),
        _score("SEC_B", date_two, "0.4"),
        _score("SEC_C", date_two, "0.2"),
    ]

    result = build_rank_stability_from_factor_scores(factor_scores)

    assert result is not None
    assert result.top_decile_persistence == Decimal("1")
    assert result.turnover_rate == Decimal("0")
    assert result.rank_correlations
    assert result.rank_correlations[0] == Decimal("1")


def test_build_rank_stability_requires_multiple_dates() -> None:
    assert build_rank_stability_from_factor_scores(
        [_score("SEC_A", date(2020, 1, 31), "0.5")]
    ) is None
