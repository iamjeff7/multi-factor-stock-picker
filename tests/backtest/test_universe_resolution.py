"""Universe resolution tests."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from backtest.experiment_config import SignalConfig, SingleFactorExperimentConfig
from backtest.experiment_runner import SingleFactorExperimentRunner
from backtest.factor_evaluation_config import FactorEvaluationSettings
from backtest.universe_resolution import (
    demo_universe_settings,
    resolve_experiment_securities,
    with_resolved_securities,
)
from config.models import UniverseSettings
from core.enums import (
    PortfolioMode,
    PositionSizeMethod,
    RebalanceFrequency,
    ResearchMode,
    ResearchPhase,
    SampleScope,
)
from core.exceptions import ValidationError
from core.types import SecurityId, Ticker
from data.loaders import ParquetLoader
from data.store import InMemoryDataStore
from entry_signals.momentum.momentum_12_1 import Momentum12_1EntrySignal
from exit_signals.examples.stub_exit_signal import ExampleStubExitSignal
from research.config import ResearchSettings


def test_resolve_experiment_securities_returns_explicit_list() -> None:
    from backtest.experiment_config import ExperimentSecurity

    config = SingleFactorExperimentConfig(
        experiment_name="explicit",
        start_date=date(2020, 1, 2),
        end_date=date(2020, 1, 10),
        portfolio_mode=PortfolioMode.SINGLE,
        securities=[
            ExperimentSecurity(security_id=SecurityId("SEC_TEST"), ticker=Ticker("TEST")),
        ],
        entry_signal=SignalConfig(name="example_stub"),
        exit_signal=SignalConfig(name="example_stub_exit"),
        research=ResearchSettings(
            research_mode=ResearchMode.TEST,
            research_phase=ResearchPhase.VALIDATION,
            sample_scope=SampleScope.FULL,
        ),
    )

    class EmptyAccess:
        @property
        def data_version(self):
            from core.types import DataVersion

            return DataVersion("test")

        def list_security_ids(self):
            return []

        def get_prices(self, *args, **kwargs):
            return []

        def get_fundamentals(self, *args, **kwargs):
            return []

        def get_corporate_actions(self, *args, **kwargs):
            return []

        def get_metadata(self, *args, **kwargs):
            return None

        def get_delisting_info(self, *args, **kwargs):
            return None

    resolved = resolve_experiment_securities(config, EmptyAccess())  # type: ignore[arg-type]

    assert len(resolved) == 1
    assert resolved[0].ticker == Ticker("TEST")


def test_resolve_experiment_securities_from_mag7_universe() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "data" / "mag7"
    if not fixture_dir.exists():
        pytest.skip("Mag7 fixture unavailable")

    config = SingleFactorExperimentConfig(
        experiment_name="mag7_universe",
        start_date=date(2020, 1, 2),
        end_date=date(2024, 12, 31),
        portfolio_mode=PortfolioMode.SINGLE,
        position_size_method=PositionSizeMethod.EQUAL_WEIGHT,
        universe=demo_universe_settings(),
        entry_signal=SignalConfig(name="momentum_12_1"),
        exit_signal=SignalConfig(name="momentum_exit_stack"),
        research=ResearchSettings(
            research_mode=ResearchMode.DEMO,
            research_phase=ResearchPhase.VALIDATION,
            sample_scope=SampleScope.FULL,
        ),
    )
    store = InMemoryDataStore(ParquetLoader().load(fixture_dir))

    resolved = resolve_experiment_securities(config, store, evaluation_date=date(2020, 7, 1))

    assert len(resolved) == 7
    assert {security.ticker for security in resolved} == {
        Ticker("AAPL"),
        Ticker("MSFT"),
        Ticker("GOOGL"),
        Ticker("AMZN"),
        Ticker("META"),
        Ticker("NVDA"),
        Ticker("TSLA"),
    }


def test_with_resolved_securities_rejects_top_n_above_universe_size() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "data" / "mag7"
    if not fixture_dir.exists():
        pytest.skip("Mag7 fixture unavailable")

    config = SingleFactorExperimentConfig(
        experiment_name="mag7_universe",
        start_date=date(2020, 1, 2),
        end_date=date(2024, 12, 31),
        portfolio_mode=PortfolioMode.SINGLE,
        top_n=10,
        universe=UniverseSettings(minimum_trading_history_days=252),
        entry_signal=SignalConfig(name="momentum_12_1"),
        exit_signal=SignalConfig(name="momentum_exit_stack"),
        research=ResearchSettings(
            research_mode=ResearchMode.DEMO,
            research_phase=ResearchPhase.VALIDATION,
            sample_scope=SampleScope.FULL,
        ),
    )
    store = InMemoryDataStore(ParquetLoader().load(fixture_dir))

    with pytest.raises(ValidationError, match="top_n cannot exceed"):
        with_resolved_securities(config, store)


def test_experiment_runner_resolves_universe_config(tmp_path: Path) -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "data" / "mag7"
    if not fixture_dir.exists():
        pytest.skip("Mag7 fixture unavailable")

    config = SingleFactorExperimentConfig(
        experiment_name="mag7_universe_runner",
        start_date=date(2023, 1, 3),
        end_date=date(2023, 12, 29),
        initial_capital=100_000,
        rebalance_frequency=RebalanceFrequency.MONTHLY,
        portfolio_mode=PortfolioMode.SINGLE,
        position_size_method=PositionSizeMethod.EQUAL_WEIGHT,
        top_n=2,
        universe=demo_universe_settings(),
        entry_signal=SignalConfig(name="momentum_12_1"),
        exit_signal=SignalConfig(name="example_stub_exit", params={"max_holding_days": 63}),
        research=ResearchSettings(
            research_mode=ResearchMode.DEMO,
            research_phase=ResearchPhase.VALIDATION,
            sample_scope=SampleScope.FULL,
        ),
        factor_evaluation=FactorEvaluationSettings(
            minimum_security_count=7,
            primary_horizon=63,
            horizons=[63],
        ),
    )
    store = InMemoryDataStore(ParquetLoader().load(fixture_dir))
    result = SingleFactorExperimentRunner().run(
        config=config,
        data_access=store,
        entry_signal=Momentum12_1EntrySignal(),
        exit_signal=ExampleStubExitSignal(max_holding_days=63),
        output_dir=tmp_path,
    )

    assert result.experiment_summary.securities_requested == 7
    assert result.experiment_summary.securities_completed == 7
