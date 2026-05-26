"""Portfolio selection tests."""

from datetime import date
from decimal import Decimal

import pytest

from backtest.portfolio_selection import build_top_n_selections
from core.types import SecurityId, SignalId, Ticker
from schemas.factors import FactorScore


def _score(
    security_id: str,
    evaluation_date: date,
    factor_score: str,
    *,
    factor_rank: str | None = None,
) -> FactorScore:
    return FactorScore(
        evaluation_date=evaluation_date,
        security_id=SecurityId(security_id),
        ticker=Ticker(security_id.removeprefix("SEC_")),
        signal_id=SignalId("test"),
        factor_score=Decimal(factor_score),
        factor_rank=Decimal(factor_rank) if factor_rank is not None else None,
    )


def test_build_top_n_selections_picks_highest_scores() -> None:
    evaluation_date = date(2020, 1, 2)
    scores = [
        _score("SEC_A", evaluation_date, "0.2"),
        _score("SEC_B", evaluation_date, "0.9"),
        _score("SEC_C", evaluation_date, "0.5"),
    ]

    selections = build_top_n_selections(scores, top_n=2)

    assert selections[evaluation_date] == {SecurityId("SEC_B"), SecurityId("SEC_C")}


def test_build_top_n_selections_rejects_invalid_top_n() -> None:
    with pytest.raises(ValueError, match="top_n must be at least 1"):
        build_top_n_selections([], top_n=0)
