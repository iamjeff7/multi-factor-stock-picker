"""In-memory backtest result store."""

from __future__ import annotations

from collections.abc import Sequence

from schemas.results import (
    BacktestSummaryRecord,
    EquityCurveRecord,
    ExperimentMetadata,
    PortfolioSnapshotRecord,
    TradeRecord,
)


class InMemoryResultStore:
    """Stores backtest outputs in memory for tests and example runs."""

    def __init__(self) -> None:
        self.experiment: ExperimentMetadata | None = None
        self.trades: list[TradeRecord] = []
        self.snapshots: list[PortfolioSnapshotRecord] = []
        self.equity_curve: list[EquityCurveRecord] = []
        self.summary: BacktestSummaryRecord | None = None

    def create_experiment(self, metadata: ExperimentMetadata) -> None:
        self.experiment = metadata

    def save_trades(self, rows: Sequence[TradeRecord]) -> None:
        self.trades.extend(rows)

    def save_portfolio_snapshots(self, rows: Sequence[PortfolioSnapshotRecord]) -> None:
        self.snapshots.extend(rows)

    def save_equity_curve(self, rows: Sequence[EquityCurveRecord]) -> None:
        self.equity_curve.extend(rows)

    def save_backtest_summary(self, summary: BacktestSummaryRecord) -> None:
        self.summary = summary

    def save_entry_signal_results(self, rows: Sequence[object]) -> None:
        del rows

    def save_exit_signal_results(self, rows: Sequence[object]) -> None:
        del rows

    def save_factor_scores(self, rows: Sequence[object]) -> None:
        del rows

    def save_composite_scores(self, rows: Sequence[object]) -> None:
        del rows

    def save_portfolio_selections(self, rows: Sequence[object]) -> None:
        del rows

    def save_positions(self, rows: Sequence[object]) -> None:
        del rows

    def save_robustness_score(self, score: object) -> None:
        del score

    def save_configuration_snapshot(self, snapshot: object) -> None:
        del snapshot

    def save_version_metadata(self, metadata: object) -> None:
        del metadata
