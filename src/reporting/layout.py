"""Result storage path layout."""

from pathlib import Path


class ResultLayout:
    """Path constants for persisted experiment results."""

    ROOT = Path("results")

    ENTRY = "entry"
    EXIT = "exit"
    REPORTS = "reports"
    RANKINGS = "rankings"

    METADATA = "metadata"
    SIGNALS = "signals"
    FACTORS = "factors"
    PORTFOLIOS = "portfolios"
    TRADES = "trades"
    POSITIONS = "positions"
    SNAPSHOTS = "snapshots"
    SUMMARIES = "summaries"
    ROBUSTNESS = "robustness"

    @classmethod
    def experiment_dir(cls, experiment_id: str) -> Path:
        return cls.ROOT / experiment_id

    @classmethod
    def subdir(cls, experiment_id: str, name: str) -> Path:
        return cls.experiment_dir(experiment_id) / name
