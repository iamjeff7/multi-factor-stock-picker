"""Dataset manifest for raw data directories."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from core.exceptions import ConfigurationError


class DatasetManifest(BaseModel):
    data_version: str
    creation_timestamp: datetime
    description: str | None = None
    tickers: list[str] = Field(default_factory=list)

    @classmethod
    def load(cls, raw_dir: Path) -> DatasetManifest:
        manifest_path = raw_dir / "manifest.yaml"
        if not manifest_path.exists():
            raise ConfigurationError(f"Missing manifest.yaml in {raw_dir}")
        with manifest_path.open(encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)
        if not isinstance(raw, dict):
            raise ConfigurationError(f"Invalid manifest format in {manifest_path}")
        return cls.model_validate(raw)
