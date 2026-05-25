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
    raw_signal_value: Decimal | None = None
    factor_score: Decimal
    factor_rank: Decimal | None = None


class CompositeScore(BaseModel):
    evaluation_date: date
    security_id: SecurityId
    ticker: Ticker
    composite_score: Decimal
    composite_rank: Decimal | None = None
    factor_contributions_json: dict[str, Decimal] | None = None
