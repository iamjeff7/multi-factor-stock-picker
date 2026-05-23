"""Data access and validation interfaces."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Protocol

from core.types import DataVersion, SecurityId
from schemas.data import (
    CorporateAction,
    DelistingInfo,
    FundamentalRecord,
    PriceBar,
    SecurityMetadata,
    ValidationReport,
)


class DataAccess(Protocol):
    """Standardized point-in-time data access for all research modules."""

    @property
    def data_version(self) -> DataVersion: ...

    def get_prices(
        self,
        security_id: SecurityId,
        start_date: date,
        end_date: date,
        as_of_date: date,
    ) -> Sequence[PriceBar]: ...

    def get_fundamentals(
        self,
        security_id: SecurityId,
        as_of_date: date,
    ) -> Sequence[FundamentalRecord]: ...

    def get_corporate_actions(
        self,
        security_id: SecurityId,
        as_of_date: date,
    ) -> Sequence[CorporateAction]: ...

    def get_metadata(
        self,
        security_id: SecurityId,
        as_of_date: date,
    ) -> SecurityMetadata | None: ...

    def get_delisting_info(
        self,
        security_id: SecurityId,
    ) -> DelistingInfo | None: ...

    def list_security_ids(self) -> Sequence[SecurityId]: ...


class DataValidator(Protocol):
    """Validates datasets before research execution."""

    def validate_all(self) -> ValidationReport: ...
