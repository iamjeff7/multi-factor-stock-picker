"""Version and reproducibility metadata."""

from datetime import datetime

from pydantic import BaseModel, Field

from core.types import (
    ConfigurationHash,
    DataVersion,
    ExperimentId,
    UniverseVersion,
)


class VersionMetadata(BaseModel):
    """Tracks implementation and input versions for an experiment."""

    experiment_id: ExperimentId
    framework_version: str
    data_version: DataVersion
    universe_version: UniverseVersion
    entry_signal_versions: dict[str, str] = Field(default_factory=dict)
    exit_signal_versions: dict[str, str] = Field(default_factory=dict)
    backtest_version: str | None = None
    configuration_hash: ConfigurationHash
    execution_timestamp: datetime
