"""Result persistence interfaces."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from schemas.results import (
    BacktestSummaryRecord,
    CompositeScoreRecord,
    ConfigurationSnapshotRecord,
    EntrySignalResultRecord,
    EquityCurveRecord,
    ExitSignalResultRecord,
    ExperimentMetadata,
    FactorScoreRecord,
    PortfolioSelectionRecord,
    PortfolioSnapshotRecord,
    PositionRecord,
    RobustnessScoreRecord,
    TradeRecord,
    VersionMetadataRecord,
)


class ResultStore(Protocol):
    """Persists experiment outputs according to result schema specifications."""

    def create_experiment(self, metadata: ExperimentMetadata) -> None: ...

    def save_entry_signal_results(self, rows: Sequence[EntrySignalResultRecord]) -> None: ...

    def save_exit_signal_results(self, rows: Sequence[ExitSignalResultRecord]) -> None: ...

    def save_factor_scores(self, rows: Sequence[FactorScoreRecord]) -> None: ...

    def save_composite_scores(self, rows: Sequence[CompositeScoreRecord]) -> None: ...

    def save_portfolio_selections(self, rows: Sequence[PortfolioSelectionRecord]) -> None: ...

    def save_trades(self, rows: Sequence[TradeRecord]) -> None: ...

    def save_positions(self, rows: Sequence[PositionRecord]) -> None: ...

    def save_portfolio_snapshots(self, rows: Sequence[PortfolioSnapshotRecord]) -> None: ...

    def save_equity_curve(self, rows: Sequence[EquityCurveRecord]) -> None: ...

    def save_backtest_summary(self, summary: BacktestSummaryRecord) -> None: ...

    def save_robustness_score(self, score: RobustnessScoreRecord) -> None: ...

    def save_configuration_snapshot(self, snapshot: ConfigurationSnapshotRecord) -> None: ...

    def save_version_metadata(self, metadata: VersionMetadataRecord) -> None: ...


class SchemaValidator(Protocol):
    """Validates records before persistence."""

    def validate_entry_signal_results(self, rows: Sequence[EntrySignalResultRecord]) -> None: ...

    def validate_exit_signal_results(self, rows: Sequence[ExitSignalResultRecord]) -> None: ...

    def validate_trades(self, rows: Sequence[TradeRecord]) -> None: ...
