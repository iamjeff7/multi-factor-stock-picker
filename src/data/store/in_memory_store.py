"""Point-in-time in-memory data store."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from core.exceptions import ValidationError
from core.types import DataVersion, SecurityId
from data.loaders.dataset import LoadedDataset
from schemas.data import (
    CorporateAction,
    DelistingInfo,
    FundamentalRecord,
    PriceBar,
    SecurityMetadata,
)


class InMemoryDataStore:
    """Implements DataAccess over a LoadedDataset with point-in-time filtering."""

    def __init__(self, dataset: LoadedDataset) -> None:
        self._dataset = dataset

    @property
    def data_version(self) -> DataVersion:
        return DataVersion(self._dataset.manifest.data_version)

    @property
    def dataset(self) -> LoadedDataset:
        return self._dataset

    def get_prices(
        self,
        security_id: SecurityId,
        start_date: date,
        end_date: date,
        as_of_date: date,
    ) -> Sequence[PriceBar]:
        if end_date > as_of_date:
            raise ValidationError(
                f"end_date {end_date} exceeds as_of_date {as_of_date} for {security_id}"
            )
        bars = self._dataset.prices.get(security_id, [])
        return [
            bar
            for bar in bars
            if start_date <= bar.trade_date <= end_date and bar.trade_date <= as_of_date
        ]

    def get_fundamentals(
        self,
        security_id: SecurityId,
        as_of_date: date,
    ) -> Sequence[FundamentalRecord]:
        records = self._dataset.fundamentals.get(security_id, [])
        return [record for record in records if record.availability_date <= as_of_date]

    def get_corporate_actions(
        self,
        security_id: SecurityId,
        as_of_date: date,
    ) -> Sequence[CorporateAction]:
        actions = self._dataset.corporate_actions.get(security_id, [])
        return [action for action in actions if action.action_date <= as_of_date]

    def get_metadata(
        self,
        security_id: SecurityId,
        as_of_date: date,
    ) -> SecurityMetadata | None:
        rows = self._dataset.metadata.get(security_id, [])
        eligible = [row for row in rows if row.as_of_date <= as_of_date]
        if not eligible:
            return None
        return max(eligible, key=lambda row: row.as_of_date)

    def get_delisting_info(self, security_id: SecurityId) -> DelistingInfo | None:
        return self._dataset.delistings.get(security_id)

    def list_security_ids(self) -> list[SecurityId]:
        return self._dataset.security_ids
