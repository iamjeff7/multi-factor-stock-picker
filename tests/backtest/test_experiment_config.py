"""Single-factor experiment config validation tests."""

from datetime import date
from decimal import Decimal

import pytest

from backtest.experiment_config import (
    ExperimentSecurity,
    SignalConfig,
    SingleFactorExperimentConfig,
)
from core.enums import (
    PortfolioMode,
    PositionSizeMethod,
    RebalanceFrequency,
    ResearchPhase,
    SampleScope,
)
from core.types import SecurityId, Ticker
from research.config import ResearchSettings


def test_experiment_config_rejects_empty_securities_without_universe() -> None:
    with pytest.raises(ValueError, match="Provide securities or universe settings"):
        SingleFactorExperimentConfig(
            experiment_name="missing_universe",
            start_date=date(2020, 1, 2),
            end_date=date(2020, 1, 8),
            portfolio_mode=PortfolioMode.SINGLE,
            entry_signal=SignalConfig(name="example_stub"),
            exit_signal=SignalConfig(name="example_stub_exit"),
            research=ResearchSettings(
                research_phase=ResearchPhase.VALIDATION,
                sample_scope=SampleScope.FULL,
            ),
        )


def test_experiment_config_rejects_discovery_with_full_scope() -> None:
    with pytest.raises(ValueError, match="DISCOVERY phase requires sample_scope=IS"):
        SingleFactorExperimentConfig(
            experiment_name="invalid_discovery",
            start_date=date(2020, 1, 2),
            end_date=date(2020, 1, 8),
            initial_capital=10_000,
            rebalance_frequency=RebalanceFrequency.DAILY,
            portfolio_mode=PortfolioMode.SINGLE,
            position_size_method=PositionSizeMethod.FIXED_DOLLAR,
            fixed_dollar_amount=Decimal("1000"),
            securities=[
                ExperimentSecurity(security_id=SecurityId("SEC_TEST"), ticker=Ticker("TEST")),
            ],
            entry_signal=SignalConfig(name="example_stub"),
            exit_signal=SignalConfig(name="example_stub_exit", params={"max_holding_days": 3}),
            research=ResearchSettings(
                research_phase=ResearchPhase.DISCOVERY,
                sample_scope=SampleScope.FULL,
            ),
        )
