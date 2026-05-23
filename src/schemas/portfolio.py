"""Portfolio schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from core.enums import PositionStatus
from core.types import ExperimentId, PositionId, SecurityId, Ticker


class PortfolioSelection(BaseModel):
    rebalance_date: date
    security_id: SecurityId
    ticker: Ticker
    portfolio_rank: int
    target_weight: Decimal
    target_shares: Decimal | None = None


class Position(BaseModel):
    experiment_id: ExperimentId
    position_id: PositionId
    security_id: SecurityId
    ticker: Ticker
    entry_date: date
    entry_price: Decimal
    shares: Decimal
    current_value: Decimal | None = None
    status: PositionStatus
