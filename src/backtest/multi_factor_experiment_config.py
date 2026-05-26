"""Multi-factor experiment configuration."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import Field, model_validator

from backtest.config import SingleStockBacktestConfig
from backtest.experiment_config import ExperimentSecurity, SignalConfig
from backtest.factor_evaluation_config import FactorEvaluationSettings
from config.models import BacktestSettings, UniverseSettings
from core.enums import PortfolioMode
from core.types import SignalId
from factors.combination.config import FactorCombinationConfig
from research.config import ResearchSettings


class MultiFactorExperimentConfig(BacktestSettings):
    """Configuration for a cross-sectional multi-factor experiment."""

    experiment_name: str = "multi_factor_experiment"
    start_date: date
    end_date: date
    securities: list[ExperimentSecurity] = Field(default_factory=list)
    universe: UniverseSettings | None = None
    fixed_dollar_amount: Decimal | None = None
    entry_signals: list[SignalConfig] = Field(min_length=2)
    exit_signal: SignalConfig
    factor_combination: FactorCombinationConfig
    research: ResearchSettings = Field(default_factory=ResearchSettings)
    factor_evaluation: FactorEvaluationSettings = Field(default_factory=FactorEvaluationSettings)
    top_n: int | None = None

    @model_validator(mode="after")
    def validate_experiment_settings(self) -> MultiFactorExperimentConfig:
        if self.portfolio_mode is not PortfolioMode.SINGLE:
            raise ValueError("Multi-factor experiments require portfolio_mode=SINGLE")
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if self.universe is None and not self.securities:
            raise ValueError("Provide securities or universe settings")
        if self.top_n is not None:
            if self.top_n < 1:
                raise ValueError("top_n must be at least 1")
            if self.universe is None and self.top_n > len(self.securities):
                raise ValueError("top_n cannot exceed the number of securities")

        enabled_factors = set(self.factor_combination.enabled_factors)
        if len(enabled_factors) < 2:
            raise ValueError("factor_combination must enable at least two factors")
        if len(enabled_factors) != len(self.entry_signals):
            raise ValueError(
                "factor_combination.factor_weights must define one weight per entry signal"
            )

        signal_names = {signal.name for signal in self.entry_signals}
        weight_keys = set(self.factor_combination.factor_weights)
        if signal_names != weight_keys:
            raise ValueError("factor_weights keys must match entry_signals names")

        from research.validator import validate_research_settings

        validate_research_settings(
            self.research,
            start_date=self.start_date,
            end_date=self.end_date,
        )
        return self

    def entry_signal_ids(self) -> tuple[SignalId, ...]:
        return tuple(SignalId(signal.name) for signal in self.entry_signals)

    def to_stock_config(self, security: ExperimentSecurity) -> SingleStockBacktestConfig:
        return SingleStockBacktestConfig(
            security_id=security.security_id,
            ticker=security.ticker,
            start_date=self.start_date,
            end_date=self.end_date,
            initial_capital=self.initial_capital,
            execution_price=self.execution_price,
            commission_pct=self.commission_pct,
            commission_per_trade=self.commission_per_trade,
            slippage_pct=self.slippage_pct,
            rebalance_frequency=self.rebalance_frequency,
            portfolio_mode=self.portfolio_mode,
            position_size_method=self.position_size_method,
            fixed_dollar_amount=self.fixed_dollar_amount,
            experiment_name=self.experiment_name,
        )
