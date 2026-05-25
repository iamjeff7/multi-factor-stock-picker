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

    EXPERIMENT_METADATA = "metadata/experiment.parquet"
    CONFIGURATION_SNAPSHOT = "metadata/configuration.parquet"
    VERSION_METADATA = "metadata/version.parquet"
    ENTRY_SIGNALS = "signals/entry_signals.parquet"
    EXIT_SIGNALS = "signals/exit_signals.parquet"
    FACTOR_SCORES = "factors/factor_scores.parquet"
    COMPOSITE_SCORES = "factors/composite_scores.parquet"
    PORTFOLIO_SELECTIONS = "portfolios/selections.parquet"
    TRADES_FILE = "trades/trades.parquet"
    POSITIONS_FILE = "positions/positions.parquet"
    PORTFOLIO_SNAPSHOTS = "snapshots/portfolio_snapshots.parquet"
    EQUITY_CURVE = "snapshots/equity_curve.parquet"
    BACKTEST_SUMMARY = "summaries/backtest_summary.parquet"
    STOCK_SUMMARIES = "summaries/stock_summaries.parquet"
    EXPERIMENT_SUMMARY = "summaries/experiment_summary.parquet"
    ROBUSTNESS_SCORE = "robustness/robustness_score.parquet"
    REPORT_MANIFEST = "reports/manifest.parquet"
    EXPERIMENT_REPORT = "reports/experiment_report.json"

    @classmethod
    def experiment_dir(cls, experiment_id: str) -> Path:
        return cls.ROOT / experiment_id

    @classmethod
    def subdir(cls, experiment_id: str, name: str) -> Path:
        return cls.experiment_dir(experiment_id) / name

    @classmethod
    def artifact_path(cls, experiment_id: str, relative_path: str) -> Path:
        return cls.experiment_dir(experiment_id) / relative_path
