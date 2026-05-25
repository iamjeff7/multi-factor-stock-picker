"""Exit signal schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from core.types import DataVersion, PositionId, SecurityId, SignalId, Ticker
from schemas.enums import (
    EvaluationFrequency,
    ExitCategory,
    ExitDecision,
    ExitMissingDataPolicy,
)


class PositionContext(BaseModel):
    position_id: PositionId
    security_id: SecurityId
    ticker: Ticker
    entry_date: date
    entry_price: Decimal
    position_size: Decimal
    holding_period: int
    highest_price_since_entry: Decimal | None = None
    lowest_price_since_entry: Decimal | None = None
    unrealized_pnl: Decimal | None = None


class ExitSignalMetadata(BaseModel):
    signal_id: SignalId
    signal_name: str
    signal_description: str | None = None
    signal_category: ExitCategory
    signal_version: str
    missing_data_policy: ExitMissingDataPolicy
    evaluation_frequency: EvaluationFrequency = EvaluationFrequency.DAILY


class ExitSignalResult(BaseModel):
    evaluation_date: date
    security_id: SecurityId
    position_id: PositionId
    signal_id: SignalId
    signal_version: str
    decision: ExitDecision
    trigger_reason: str | None = None
    metadata_json: dict[str, object] | None = None


class ExitSignalRunMetadata(BaseModel):
    signal_version: str
    data_version: DataVersion
    execution_timestamp: datetime
