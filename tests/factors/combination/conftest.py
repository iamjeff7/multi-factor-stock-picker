"""Shared helpers for factor combination tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from core.types import SecurityId, SignalId, Ticker
from schemas.factors import FactorScore


def make_factor_score(
    *,
    security_id: str,
    ticker: str,
    signal_id: str,
    factor_score: Decimal,
    evaluation_date: date = date(2020, 1, 31),
) -> FactorScore:
    return FactorScore(
        evaluation_date=evaluation_date,
        security_id=SecurityId(security_id),
        ticker=Ticker(ticker),
        signal_id=SignalId(signal_id),
        factor_score=factor_score,
    )


def make_multi_factor_scores(
    scores_by_security: dict[str, dict[str, Decimal]],
    *,
    evaluation_date: date = date(2020, 1, 31),
) -> list[FactorScore]:
    rows: list[FactorScore] = []
    for security_id, factor_scores in scores_by_security.items():
        for signal_id, factor_score in factor_scores.items():
            rows.append(
                make_factor_score(
                    security_id=security_id,
                    ticker=security_id,
                    signal_id=signal_id,
                    factor_score=factor_score,
                    evaluation_date=evaluation_date,
                )
            )
    return rows
