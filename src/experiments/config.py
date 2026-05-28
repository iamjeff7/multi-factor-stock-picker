"""Unified experiment configuration."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from backtest.experiment_config import ExperimentSecurity
from backtest.factor_evaluation_config import FactorEvaluationSettings
from config.models import BacktestSettings, UniverseSettings
from core.enums import PortfolioMode, ResearchMode, ResearchPhase, SampleScope
from experiments.enums import (
    DataPreset,
    EntryCadence,
    EntryEvaluationMode,
    ExitEvaluationMode,
    ExperimentMode,
)
from experiments.ranking import DEFAULT_QUALIFYING_PERCENTILE
from research.config import ResearchSettings


class RankingSettings(BaseModel):
    qualifying_percentile: int = DEFAULT_QUALIFYING_PERCENTILE
    min_qualifying_factors: int = 1
    metric_weights: dict[str, Decimal] = Field(default_factory=dict)


class EntryExperimentSettings(BaseModel):
    exit_evaluation_mode: ExitEvaluationMode = ExitEvaluationMode.FIXED_PERIOD
    exit_horizons_months: list[int] = Field(default_factory=lambda: [3])
    forward_window_trading_months: int = 6


class ExitExperimentSettings(BaseModel):
    entry_evaluation_mode: EntryEvaluationMode = EntryEvaluationMode.FIXED_PERIOD
    entry_cadence: EntryCadence = EntryCadence.WEEK
    compute_robustness: bool = True
    baseline_holding_months: int = 3


class CombinedExperimentSettings(BaseModel):
    entry_rankings_source: Path | None = None
    exit_rankings_source: Path | None = None
    benchmark_ticker: str = "SPY"
    risk_free_source: str = "T_BILL"


class UnifiedExperimentConfig(BacktestSettings):
    experiment_name: str = "unified_experiment"
    experiment_mode: ExperimentMode
    data_preset: DataPreset = DataPreset.DEMO
    start_date: date | None = None
    end_date: date | None = None
    securities: list[ExperimentSecurity] = Field(default_factory=list)
    universe: UniverseSettings | None = None
    entry: EntryExperimentSettings = Field(default_factory=EntryExperimentSettings)
    exit: ExitExperimentSettings = Field(default_factory=ExitExperimentSettings)
    combined: CombinedExperimentSettings = Field(default_factory=CombinedExperimentSettings)
    ranking: RankingSettings = Field(default_factory=RankingSettings)
    research: ResearchSettings = Field(
        default_factory=lambda: ResearchSettings(
            research_mode=ResearchMode.DEMO,
            research_phase=ResearchPhase.VALIDATION,
            sample_scope=SampleScope.FULL,
        )
    )
    factor_evaluation: FactorEvaluationSettings = Field(
        default_factory=lambda: FactorEvaluationSettings(
            enabled=True,
            minimum_security_count=30,
            primary_horizon=63,
            horizons=[21, 63],
            compute_robustness=True,
        )
    )

    @model_validator(mode="after")
    def validate_mode(self) -> UnifiedExperimentConfig:
        if self.universe is None and not self.securities:
            raise ValueError("Provide securities or universe settings")
        if self.experiment_mode is ExperimentMode.ENTRY_AND_EXIT:
            if self.portfolio_mode is not PortfolioMode.SINGLE:
                raise ValueError("entry_and_exit mode currently requires portfolio_mode=SINGLE")
        return self
