"""Dispatch unified experiment runs by mode."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from data.protocols import DataAccess
from experiments.combined_runner import CombinedExperimentRunner
from experiments.config import UnifiedExperimentConfig
from experiments.entry_runner import EntryExperimentRunner
from experiments.enums import ExperimentMode
from experiments.exit_runner import ExitExperimentRunner


class UnifiedExperimentRunner:
    def __init__(self) -> None:
        self._entry = EntryExperimentRunner()
        self._exit = ExitExperimentRunner()
        self._combined = CombinedExperimentRunner()

    def run(
        self,
        config: UnifiedExperimentConfig,
        data_access: DataAccess,
        *,
        output_dir: Path,
        reference_date: date | None = None,
    ) -> Path:
        if config.experiment_mode is ExperimentMode.ENTRY:
            return self._entry.run(
                config,
                data_access,
                output_dir=output_dir,
                reference_date=reference_date,
            )
        if config.experiment_mode is ExperimentMode.EXIT:
            return self._exit.run(
                config,
                data_access,
                output_dir=output_dir,
                reference_date=reference_date,
            )
        if config.experiment_mode is ExperimentMode.ENTRY_AND_EXIT:
            return self._combined.run(
                config,
                data_access,
                output_dir=output_dir,
                reference_date=reference_date,
            )
        raise ValueError(f"Unsupported experiment mode: {config.experiment_mode}")
