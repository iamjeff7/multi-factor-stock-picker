"""Backtest engine interfaces."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from backtest.config import BacktestConfig
from backtest.position_sizing import PortfolioConstructor
from core.types import ExperimentId
from data.protocols import DataAccess
from data.universe.protocols import UniverseBuilder
from entry_signals.protocols import EntrySignal
from exit_signals.protocols import ExitSignal
from factors.combination.protocols import FactorCombiner
from factors.scoring.protocols import FactorScorer
from reporting.protocols import ResultStore
from schemas.backtest import BacktestSummary


class BacktestEngine(Protocol):
    """Orchestrates a full backtest run and persists results."""

    def run(
        self,
        config: BacktestConfig,
        data_access: DataAccess,
        universe_builder: UniverseBuilder,
        entry_signals: Sequence[EntrySignal],
        exit_signals: Sequence[ExitSignal],
        result_store: ResultStore,
        factor_scorer: FactorScorer | None = None,
        factor_combiner: FactorCombiner | None = None,
        portfolio_constructor: PortfolioConstructor | None = None,
    ) -> ExperimentId: ...


class PerformanceCalculator(Protocol):
    """Computes performance metrics from trades and equity curve."""

    def summarize(self, experiment_id: ExperimentId) -> BacktestSummary: ...
