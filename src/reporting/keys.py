"""Primary key field tuples for persisted result records."""

from __future__ import annotations

ENTRY_SIGNAL_RESULT_PK = (
    "experiment_id",
    "evaluation_date",
    "security_id",
    "signal_id",
)
EXIT_SIGNAL_RESULT_PK = (
    "experiment_id",
    "evaluation_date",
    "position_id",
    "signal_id",
)
FACTOR_SCORE_PK = (
    "experiment_id",
    "evaluation_date",
    "security_id",
    "signal_id",
)
COMPOSITE_SCORE_PK = (
    "experiment_id",
    "evaluation_date",
    "security_id",
)
PORTFOLIO_SELECTION_PK = (
    "experiment_id",
    "rebalance_date",
    "security_id",
)
TRADE_PK = ("experiment_id", "trade_id")
POSITION_PK = ("experiment_id", "position_id")
PORTFOLIO_SNAPSHOT_PK = ("experiment_id", "date")
EQUITY_CURVE_PK = ("experiment_id", "date")
BACKTEST_SUMMARY_PK = ("experiment_id",)
STOCK_SUMMARY_PK = ("experiment_id", "security_id")
ROBUSTNESS_SCORE_PK = ("experiment_id",)
CONFIGURATION_SNAPSHOT_PK = ("experiment_id",)
VERSION_METADATA_PK = ("experiment_id",)
REPORT_ARTIFACT_PK = ("experiment_id", "report_id")
