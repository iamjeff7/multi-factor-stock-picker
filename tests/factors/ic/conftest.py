"""Shared helpers for IC tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from core.types import SecurityId, SignalId, Ticker
from schemas.factors import FactorScore
from schemas.ic import ForwardReturn


def make_factor_score(
    *,
    security_id: str,
    factor_score: Decimal,
    signal_id: str = "momentum_12m",
    evaluation_date: date = date(2020, 1, 31),
) -> FactorScore:
    return FactorScore(
        evaluation_date=evaluation_date,
        security_id=SecurityId(security_id),
        ticker=Ticker(security_id),
        signal_id=SignalId(signal_id),
        factor_score=factor_score,
    )


def make_forward_return(
    *,
    security_id: str,
    forward_return: Decimal,
    horizon: int = 21,
    evaluation_date: date = date(2020, 1, 31),
) -> ForwardReturn:
    return ForwardReturn(
        evaluation_date=evaluation_date,
        security_id=SecurityId(security_id),
        horizon=horizon,
        forward_return=forward_return,
    )
