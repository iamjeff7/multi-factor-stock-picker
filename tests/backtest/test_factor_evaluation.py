"""Factor evaluation tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from backtest.experiment_config import (
    ExperimentSecurity,
    SignalConfig,
    SingleFactorExperimentConfig,
)
from backtest.experiment_runner import SingleFactorExperimentRunner
from backtest.factor_evaluation import SingleFactorFactorEvaluator
from backtest.factor_evaluation_config import FactorEvaluationSettings
from core.enums import (
    PortfolioMode,
    PositionSizeMethod,
    RebalanceFrequency,
    ResearchMode,
    ResearchPhase,
    SampleScope,
)
from core.types import DataVersion, ExperimentId, SecurityId, Ticker
from data.loaders import ParquetLoader
from data.store import InMemoryDataStore
from entry_signals.momentum.momentum_12_1 import Momentum12_1EntrySignal
from exit_signals.examples.stub_exit_signal import ExampleStubExitSignal
from research.config import ResearchSettings
from research.sample_split import collect_trading_days_from_data, compute_sample_split


class MultiSecurityDataAccess:
    def __init__(self, prices_by_security: dict[SecurityId, dict[date, Decimal]]) -> None:
        self._prices = prices_by_security

    @property
    def data_version(self) -> DataVersion:
        return DataVersion("test_multi_001")

    def get_prices(
        self,
        security_id: SecurityId,
        start_date: date,
        end_date: date,
        as_of_date: date,
    ):
        from schemas.data import PriceBar

        bars = []
        for trade_date, close in sorted(self._prices.get(security_id, {}).items()):
            if start_date <= trade_date <= end_date and trade_date <= as_of_date:
                bars.append(
                    PriceBar(
                        trade_date=trade_date,
                        open=close,
                        high=close,
                        low=close,
                        close=close,
                        adjusted_close=close,
                        volume=1_000,
                    )
                )
        return bars

    def get_fundamentals(self, security_id: SecurityId, as_of_date: date):
        del security_id, as_of_date
        return []

    def get_corporate_actions(self, security_id: SecurityId, as_of_date: date):
        del security_id, as_of_date
        return []

    def get_metadata(self, security_id: SecurityId, as_of_date: date):
        del security_id, as_of_date
        return None

    def get_delisting_info(self, security_id: SecurityId):
        del security_id
        return None

    def list_security_ids(self) -> list[SecurityId]:
        return list(self._prices)


def _build_cross_sectional_prices(
    *,
    security_ids: list[SecurityId],
    start_date: date,
    day_count: int,
) -> dict[SecurityId, dict[date, Decimal]]:
    prices: dict[SecurityId, dict[date, Decimal]] = {}
    for index, security_id in enumerate(security_ids):
        base = Decimal("100") + Decimal(index * 10)
        daily_return = Decimal("1.001") + Decimal(index) * Decimal("0.0001")
        price = base
        security_prices: dict[date, Decimal] = {}
        for offset in range(day_count):
            trade_date = start_date + _timedelta_days(offset)
            security_prices[trade_date] = price
            price *= daily_return
        prices[security_id] = security_prices
    return prices


def _timedelta_days(offset: int):
    from datetime import timedelta

    return timedelta(days=offset)


def test_factor_evaluator_scores_and_computes_ic() -> None:
    security_ids = [SecurityId(f"SEC_{index}") for index in range(7)]
    start_date = date(2020, 1, 1)
    day_count = 400
    data_access = MultiSecurityDataAccess(
        _build_cross_sectional_prices(
            security_ids=security_ids,
            start_date=start_date,
            day_count=day_count,
        )
    )
    config = SingleFactorExperimentConfig(
        experiment_name="factor_eval_test",
        start_date=date(2020, 7, 1),
        end_date=date(2020, 12, 31),
        initial_capital=10_000,
        rebalance_frequency=RebalanceFrequency.MONTHLY,
        portfolio_mode=PortfolioMode.SINGLE,
        position_size_method=PositionSizeMethod.EQUAL_WEIGHT,
        securities=[
            ExperimentSecurity(security_id=security_id, ticker=Ticker(f"T{index}"))
            for index, security_id in enumerate(security_ids)
        ],
        entry_signal=SignalConfig(name="momentum_12_1"),
        exit_signal=SignalConfig(name="example_stub_exit", params={"max_holding_days": 63}),
        research=ResearchSettings(
            research_mode=ResearchMode.TEST,
            research_phase=ResearchPhase.VALIDATION,
            sample_scope=SampleScope.FULL,
        ),
        factor_evaluation=FactorEvaluationSettings(
            minimum_security_count=7,
            primary_horizon=21,
            horizons=[21],
        ),
    )
    trading_days = collect_trading_days_from_data(
        data_access,
        security_ids,
        calendar_start=config.start_date,
        calendar_end=config.end_date,
    )
    split = compute_sample_split(
        trading_days,
        calendar_start=config.start_date,
        calendar_end=config.end_date,
    )

    result, entry_records, score_records = SingleFactorFactorEvaluator().evaluate(
        config=config,
        data_access=data_access,
        entry_signal=Momentum12_1EntrySignal(),
        trading_days=trading_days,
        split=split,
        settings=config.factor_evaluation,
        experiment_id=ExperimentId("exp_test"),
    )

    assert result is not None
    assert result.scoring_summary.evaluation_dates > 0
    assert result.scoring_summary.total_scores > 0
    assert result.ic_analysis is not None
    assert result.ic_analysis.full_summary is not None
    assert len(entry_records) > 0
    assert len(score_records) > 0


def test_experiment_runner_includes_factor_metrics_on_mag7(tmp_path: Path) -> None:
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "data" / "mag7"
    if not fixture_dir.exists():
        pytest.skip("Mag7 fixture unavailable")

    config = SingleFactorExperimentConfig(
        experiment_name="mag7_factor_eval",
        start_date=date(2023, 1, 3),
        end_date=date(2023, 12, 29),
        initial_capital=100_000,
        rebalance_frequency=RebalanceFrequency.MONTHLY,
        portfolio_mode=PortfolioMode.SINGLE,
        position_size_method=PositionSizeMethod.EQUAL_WEIGHT,
        securities=[
            ExperimentSecurity(security_id=SecurityId("SEC_AAPL"), ticker=Ticker("AAPL")),
            ExperimentSecurity(security_id=SecurityId("SEC_MSFT"), ticker=Ticker("MSFT")),
            ExperimentSecurity(security_id=SecurityId("SEC_GOOGL"), ticker=Ticker("GOOGL")),
            ExperimentSecurity(security_id=SecurityId("SEC_AMZN"), ticker=Ticker("AMZN")),
            ExperimentSecurity(security_id=SecurityId("SEC_META"), ticker=Ticker("META")),
            ExperimentSecurity(security_id=SecurityId("SEC_NVDA"), ticker=Ticker("NVDA")),
            ExperimentSecurity(security_id=SecurityId("SEC_TSLA"), ticker=Ticker("TSLA")),
        ],
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

    assert result.factor_evaluation is not None
    assert result.factor_evaluation.scoring_summary.total_scores > 0

    report_path = tmp_path / str(result.experiment_id) / "reports" / "experiment_report.json"
    assert report_path.exists()
    report_text = report_path.read_text(encoding="utf-8")
    assert "factor_scoring" in report_text
    assert "factor_ic" in report_text
    assert "entry_robustness" in report_text
    assert result.factor_evaluation.entry_robustness is not None


def test_experiment_runner_top_n_reduces_trades() -> None:
    security_ids = [SecurityId(f"SEC_{index}") for index in range(7)]
    start_date = date(2020, 1, 1)
    day_count = 400
    data_access = MultiSecurityDataAccess(
        _build_cross_sectional_prices(
            security_ids=security_ids,
            start_date=start_date,
            day_count=day_count,
        )
    )
    base_kwargs = dict(
        experiment_name="top_n_test",
        start_date=date(2020, 7, 1),
        end_date=date(2020, 12, 31),
        initial_capital=10_000,
        rebalance_frequency=RebalanceFrequency.MONTHLY,
        portfolio_mode=PortfolioMode.SINGLE,
        position_size_method=PositionSizeMethod.EQUAL_WEIGHT,
        securities=[
            ExperimentSecurity(security_id=security_id, ticker=Ticker(f"T{index}"))
            for index, security_id in enumerate(security_ids)
        ],
        entry_signal=SignalConfig(name="momentum_12_1"),
        exit_signal=SignalConfig(name="example_stub_exit", params={"max_holding_days": 63}),
        research=ResearchSettings(
            research_mode=ResearchMode.TEST,
            research_phase=ResearchPhase.VALIDATION,
            sample_scope=SampleScope.FULL,
        ),
        factor_evaluation=FactorEvaluationSettings(
            minimum_security_count=7,
            primary_horizon=21,
            horizons=[21],
        ),
    )
    runner = SingleFactorExperimentRunner()
    unrestricted = runner.run(
        config=SingleFactorExperimentConfig(**base_kwargs),
        data_access=data_access,
        entry_signal=Momentum12_1EntrySignal(),
        exit_signal=ExampleStubExitSignal(max_holding_days=63),
    )
    restricted = runner.run(
        config=SingleFactorExperimentConfig(**base_kwargs, top_n=1),
        data_access=data_access,
        entry_signal=Momentum12_1EntrySignal(),
        exit_signal=ExampleStubExitSignal(max_holding_days=63),
    )

    assert (
        restricted.experiment_summary.number_of_trades
        < unrestricted.experiment_summary.number_of_trades
    )
