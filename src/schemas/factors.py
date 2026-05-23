"""Factor score schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from core.types import SecurityId, SignalId, Ticker


class FactorScore(BaseModel):
    evaluation_date: date
    security_id: SecurityId
    ticker: Ticker
    signal_id: SignalId
    factor_score: Decimal
    factor_rank: int | None = None


class CompositeScore(BaseModel):
    evaluation_date: date
    security_id: SecurityId
    ticker: Ticker
    composite_score: Decimal
    composite_rank: int | None = None
