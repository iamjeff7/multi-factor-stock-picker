"""Entry signal schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, model_validator

from core.types import DataVersion, SecurityId, SignalId, Ticker, UniverseVersion
from schemas.enums import SignalCategory, SignalDirection


class SignalMetadata(BaseModel):
    signal_id: SignalId
    signal_name: str
    signal_description: str | None = None
    signal_category: SignalCategory
    signal_version: str
    higher_is_better: bool | None = None
    lower_is_better: bool | None = None

    @model_validator(mode="after")
    def validate_direction(self) -> SignalMetadata:
        if self.higher_is_better is None and self.lower_is_better is None:
            raise ValueError("Signal must define higher_is_better or lower_is_better")
        return self

    @property
    def direction(self) -> SignalDirection:
        if self.higher_is_better:
            return SignalDirection.HIGHER_IS_BETTER
        return SignalDirection.LOWER_IS_BETTER


class EntrySignalResult(BaseModel):
    evaluation_date: date
    security_id: SecurityId
    ticker: Ticker
    signal_id: SignalId
    signal_version: str
    raw_signal_value: Decimal | None
    metadata_json: dict[str, object] | None = None


class EntrySignalRunMetadata(BaseModel):
    signal_version: str
    data_version: DataVersion
    universe_version: UniverseVersion
    execution_timestamp: datetime
