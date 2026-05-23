"""Market and reference data schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from core.types import SecurityId, Ticker


class PriceBar(BaseModel):
    trade_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adjusted_close: Decimal
    volume: int
    vwap: Decimal | None = None
    dollar_volume: Decimal | None = None


class CorporateAction(BaseModel):
    security_id: SecurityId
    action_date: date
    action_type: Literal["SPLIT", "REVERSE_SPLIT", "CASH_DIVIDEND", "SPECIAL_DIVIDEND"]
    ratio: Decimal | None = None
    amount: Decimal | None = None


class FundamentalRecord(BaseModel):
    security_id: SecurityId
    metric_name: str
    reporting_period_end: date
    filing_date: date
    availability_date: date
    value: Decimal | None


class SecurityMetadata(BaseModel):
    security_id: SecurityId
    ticker: Ticker
    permanent_security_id: str
    company_name: str
    exchange: str
    sector: str | None = None
    industry: str | None = None
    as_of_date: date


class DelistingInfo(BaseModel):
    security_id: SecurityId
    delisting_date: date
    delisting_reason: str


class ValidationIssue(BaseModel):
    check_name: str
    message: str
    security_id: SecurityId | None = None


class ValidationReport(BaseModel):
    passed: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
    validated_at: datetime
