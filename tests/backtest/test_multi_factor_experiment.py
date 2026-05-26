"""Multi-factor experiment tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from backtest.experiment_config import ExperimentSecurity, SignalConfig
from backtest.factor_combination_flow import score_and_combine_multi_factor
from backtest.factor_evaluation_config import FactorEvaluationSettings
from backtest.multi_factor_experiment_config import MultiFactorExperimentConfig
from backtest.multi_factor_experiment_runner import MultiFactorExperimentRunner
from backtest.portfolio_selection import build_top_n_selections_from_composite
from backtest.signal_factory import build_entry_signals
from core.enums import (
    PortfolioMode,
    PositionSizeMethod,
    RebalanceFrequency,
    ResearchMode,
    ResearchPhase,
    SampleScope,
)
from core.types import SecurityId, Ticker
from data.loaders import ParquetLoader
from data.store import InMemoryDataStore
from exit_signals.examples.stub_exit_signal import ExampleStubExitSignal
from factors.combination.config import FactorCombinationConfig
from research.config import ResearchSettings


def _mag7_securities() -> list[ExperimentSecurity]:
    return [
        ExperimentSecurity(security_id=SecurityId(f"SEC_{ticker}"), ticker=Ticker(ticker))
        for ticker in ("AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA")
    ]


def _multi_factor_config() -> MultiFactorExperimentConfig:
    return MultiFactorExperimentConfig(
        experiment_name="mag7_multi_momentum",
        start_date=date(2023, 1, 3),
        end_date=date(2023, 12, 29),
        initial_capital=100_000,
        rebalance_frequency=RebalanceFrequency.MONTHLY,
        portfolio_mode=PortfolioMode.SINGLE,
        position_size_method=PositionSizeMethod.EQUAL_WEIGHT,
        top_n=2,
        securities=_mag7_securities(),
        entry_signals=[
            SignalConfig(name="momentum_12_1"),
            SignalConfig(name="momentum_6_1"),
        ],
        exit_signal=SignalConfig(name="example_stub_exit", params={"max_holding_days": 63}),
        factor_combination=FactorCombinationConfig(
            factor_weights={
                "momentum_12_1": Decimal("1"),
                "momentum_6_1": Decimal("1"),
            }
        ),
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


def test_score_and_combine_multi_factor_on_mag7() -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "data" / "mag7"
    if not fixture_dir.exists():
        pytest.skip("Mag7 fixture unavailable")

    config = _multi_factor_config()
    store = InMemoryDataStore(ParquetLoader().load(fixture_dir))
    entry_signals = build_entry_signals(config.entry_signals)
    from research.sample_split import collect_trading_days_from_data

    trading_days = collect_trading_days_from_data(
        store,
        [security.security_id for security in config.securities],
        calendar_start=config.start_date,
        calendar_end=config.end_date,
    )

    result = score_and_combine_multi_factor(
        config=config,
        data_access=store,
        entry_signals=entry_signals,
        trading_days=trading_days,
        settings=config.factor_evaluation,
    )

    assert result is not None
    assert len(result.factor_scores) > 0
    assert len(result.composite_scores) > 0
    signal_ids = {str(row.signal_id) for row in result.factor_scores}
    assert signal_ids == {"momentum_12_1", "momentum_6_1"}


def test_build_top_n_selections_from_composite() -> None:
    from schemas.factors import CompositeScore

    rows = [
        CompositeScore(
            evaluation_date=date(2023, 1, 31),
            security_id=SecurityId("SEC_A"),
            ticker=Ticker("A"),
            composite_score=Decimal("0.9"),
            composite_rank=Decimal("1"),
        ),
        CompositeScore(
            evaluation_date=date(2023, 1, 31),
            security_id=SecurityId("SEC_B"),
            ticker=Ticker("B"),
            composite_score=Decimal("0.5"),
            composite_rank=Decimal("2"),
        ),
        CompositeScore(
            evaluation_date=date(2023, 1, 31),
            security_id=SecurityId("SEC_C"),
            ticker=Ticker("C"),
            composite_score=Decimal("0.1"),
            composite_rank=Decimal("3"),
        ),
    ]

    selections = build_top_n_selections_from_composite(rows, top_n=2)

    assert selections[date(2023, 1, 31)] == {SecurityId("SEC_A"), SecurityId("SEC_B")}


def test_multi_factor_experiment_runner_on_mag7(tmp_path: Path) -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "data" / "mag7"
    if not fixture_dir.exists():
        pytest.skip("Mag7 fixture unavailable")

    config = _multi_factor_config()
    store = InMemoryDataStore(ParquetLoader().load(fixture_dir))
    result = MultiFactorExperimentRunner().run(
        config=config,
        data_access=store,
        entry_signals=build_entry_signals(config.entry_signals),
        exit_signal=ExampleStubExitSignal(max_holding_days=63),
        output_dir=tmp_path,
    )

    assert result.experiment_summary.securities_completed == 7
    assert result.factor_combination is not None
    assert result.factor_combination.summary.total_composite_scores > 0
    assert set(result.factor_combination.summary.factor_signal_ids) == {
        "momentum_12_1",
        "momentum_6_1",
    }

    report_path = tmp_path / str(result.experiment_id) / "reports" / "experiment_report.json"
    assert report_path.exists()
    assert "factor_combination" in report_path.read_text(encoding="utf-8")

    composite_path = (
        tmp_path / str(result.experiment_id) / "factors" / "composite_scores.parquet"
    )
    assert composite_path.exists()
