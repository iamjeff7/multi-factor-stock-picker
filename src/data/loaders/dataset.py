"""In-memory representation of a loaded dataset."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.types import SecurityId
from data.loaders.manifest import DatasetManifest
from schemas.data import (
    CorporateAction,
    DelistingInfo,
    FundamentalRecord,
    PriceBar,
    SecurityMetadata,
)


@dataclass
class LoadedDataset:
    manifest: DatasetManifest
    prices: dict[SecurityId, list[PriceBar]] = field(default_factory=dict)
    fundamentals: dict[SecurityId, list[FundamentalRecord]] = field(default_factory=dict)
    corporate_actions: dict[SecurityId, list[CorporateAction]] = field(default_factory=dict)
    metadata: dict[SecurityId, list[SecurityMetadata]] = field(default_factory=dict)
    delistings: dict[SecurityId, DelistingInfo] = field(default_factory=dict)

    @property
    def security_ids(self) -> list[SecurityId]:
        ids: set[SecurityId] = set()
        ids.update(self.prices.keys())
        ids.update(self.metadata.keys())
        ids.update(self.fundamentals.keys())
        ids.update(self.corporate_actions.keys())
        ids.update(self.delistings.keys())
        return sorted(ids, key=str)
