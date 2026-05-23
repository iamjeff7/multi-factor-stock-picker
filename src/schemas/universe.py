"""Universe membership schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from core.types import ConfigurationHash, DataVersion, SecurityId, Ticker, UniverseVersion


class UniverseMembership(BaseModel):
    evaluation_date: date
    security_id: SecurityId
    ticker: Ticker
    is_member: bool
    membership_reason: str | None = None
    exchange: str | None = None
    sector: str | None = None
    industry: str | None = None
    market_cap: Decimal | None = None
    average_daily_dollar_volume: Decimal | None = None


class UniverseMetadata(BaseModel):
    universe_version: UniverseVersion
    creation_timestamp: datetime
    configuration_hash: ConfigurationHash
    data_version: DataVersion


class UniverseMembershipSnapshot(BaseModel):
    evaluation_date: date
    memberships: list[UniverseMembership] = Field(default_factory=list)
    metadata: UniverseMetadata
