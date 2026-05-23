"""Research dataset snapshot for experiment reproducibility."""

from datetime import datetime

from pydantic import BaseModel

from core.types import DataVersion, UniverseVersion


class ResearchDatasetSnapshot(BaseModel):
    """Records dataset versions used for an experiment run."""

    data_version: DataVersion
    universe_version: UniverseVersion
    execution_timestamp: datetime
