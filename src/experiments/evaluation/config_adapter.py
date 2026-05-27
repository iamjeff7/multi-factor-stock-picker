"""Adapt unified experiment config for backtest factor evaluation."""

from __future__ import annotations

from backtest.experiment_config import SignalConfig, SingleFactorExperimentConfig
from backtest.factor_evaluation_config import FactorEvaluationSettings
from core.enums import PortfolioMode
from experiments.config import UnifiedExperimentConfig
from experiments.signal_catalog import SignalVariant

TRADING_DAYS_PER_MONTH = 21
_STUB_EXIT_SIGNAL = SignalConfig(name="example_stub_exit", params={"max_holding_days": 63})


def resolve_factor_evaluation_settings(
    settings: FactorEvaluationSettings,
    *,
    security_count: int,
    exit_horizon_months: int,
) -> FactorEvaluationSettings:
    """Align IC horizons with the entry exit horizon and fit the available universe."""
    resolved = settings.model_copy(deep=True)
    primary_horizon = exit_horizon_months * TRADING_DAYS_PER_MONTH
    horizons = set(resolved.horizons)
    horizons.add(primary_horizon)
    resolved.horizons = sorted(horizons)
    resolved.primary_horizon = primary_horizon
    resolved.minimum_security_count = min(
        resolved.minimum_security_count,
        max(security_count, 2),
    )
    return resolved


def to_single_factor_config(
    config: UnifiedExperimentConfig,
    *,
    variant: SignalVariant,
    factor_evaluation: FactorEvaluationSettings,
) -> SingleFactorExperimentConfig:
    """Build the minimal single-factor config required by SingleFactorFactorEvaluator."""
    if config.start_date is None or config.end_date is None:
        raise ValueError("start_date and end_date must be resolved before factor evaluation")

    return SingleFactorExperimentConfig(
        experiment_name=config.experiment_name,
        start_date=config.start_date,
        end_date=config.end_date,
        initial_capital=config.initial_capital,
        execution_price=config.execution_price,
        commission_pct=config.commission_pct,
        commission_per_trade=config.commission_per_trade,
        slippage_pct=config.slippage_pct,
        rebalance_frequency=config.rebalance_frequency,
        portfolio_mode=PortfolioMode.SINGLE,
        position_size_method=config.position_size_method,
        securities=config.securities,
        universe=config.universe,
        entry_signal=variant.config,
        exit_signal=_STUB_EXIT_SIGNAL,
        research=config.research,
        factor_evaluation=factor_evaluation,
    )
