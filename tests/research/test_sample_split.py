"""Tests for in-sample / out-of-sample sample split utilities."""

from datetime import date
from decimal import Decimal

import pytest

from core.enums import ResearchPhase, SamplePeriod, SampleScope
from core.types import ExperimentId, SecurityId, Ticker, TradeId
from research.config import ResearchSettings
from research.degradation import compute_degradation_metrics
from research.sample_split import (
    classify_date,
    compute_sample_split,
    filter_trades_by_period,
    last_completed_calendar_year_end,
)
from research.validator import validate_research_settings
from schemas.results import ExperimentSummaryRecord, TradeRecord


def test_compute_sample_split_uses_trading_day_fraction() -> None:
    trading_days = [date(2020, 1, d) for d in range(2, 12)]

    split = compute_sample_split(
        trading_days,
        calendar_start=date(2020, 1, 2),
        calendar_end=date(2020, 1, 11),
        is_fraction=Decimal("0.80"),
    )

    assert split.is_trading_days == 8
    assert split.oos_trading_days == 2
    assert split.split_date == date(2020, 1, 10)
    assert classify_date(date(2020, 1, 9), split) is SamplePeriod.IN_SAMPLE
    assert classify_date(date(2020, 1, 10), split) is SamplePeriod.OUT_OF_SAMPLE


def test_filter_trades_by_period_uses_exit_date() -> None:
    split = compute_sample_split(
        [date(2020, 1, 2), date(2020, 1, 3), date(2020, 1, 6), date(2020, 1, 7)],
        calendar_start=date(2020, 1, 2),
        calendar_end=date(2020, 1, 7),
    )
    is_trade = TradeRecord(
        experiment_id=ExperimentId("exp_test"),
        trade_id=TradeId("trade_is"),
        security_id=SecurityId("SEC_TEST"),
        ticker=Ticker("TEST"),
        entry_date=date(2020, 1, 2),
        entry_price=Decimal("100"),
        exit_date=date(2020, 1, 3),
        exit_price=Decimal("101"),
        shares=Decimal("10"),
        net_pnl=Decimal("10"),
    )
    oos_trade = TradeRecord(
        experiment_id=ExperimentId("exp_test"),
        trade_id=TradeId("trade_oos"),
        security_id=SecurityId("SEC_TEST"),
        ticker=Ticker("TEST"),
        entry_date=date(2020, 1, 6),
        entry_price=Decimal("100"),
        exit_date=date(2020, 1, 7),
        exit_price=Decimal("102"),
        shares=Decimal("10"),
        net_pnl=Decimal("20"),
    )

    is_trades = filter_trades_by_period(
        [is_trade, oos_trade],
        split=split,
        sample_period=SamplePeriod.IN_SAMPLE,
    )
    oos_trades = filter_trades_by_period(
        [is_trade, oos_trade],
        split=split,
        sample_period=SamplePeriod.OUT_OF_SAMPLE,
    )

    assert len(is_trades) == 1
    assert len(oos_trades) == 1
    assert is_trades[0].exit_date == date(2020, 1, 3)
    assert oos_trades[0].exit_date == date(2020, 1, 7)


def test_discovery_rejects_oos_scope() -> None:
    settings = ResearchSettings(
        research_phase=ResearchPhase.DISCOVERY,
        sample_scope=SampleScope.FULL,
    )
    with pytest.raises(ValueError, match="DISCOVERY phase requires sample_scope=IS"):
        validate_research_settings(
            settings,
            start_date=date(2023, 1, 3),
            end_date=date(2023, 6, 30),
        )


def test_discovery_rejects_end_date_in_oos_window() -> None:
    split = compute_sample_split(
        [date(2020, 1, d) for d in range(2, 12)],
        calendar_start=date(2020, 1, 2),
        calendar_end=date(2020, 1, 11),
    )
    settings = ResearchSettings(
        research_phase=ResearchPhase.DISCOVERY,
        sample_scope=SampleScope.IN_SAMPLE,
    )
    with pytest.raises(ValueError, match="DISCOVERY runs must end before OOS split_date"):
        validate_research_settings(
            settings,
            start_date=date(2020, 1, 2),
            end_date=date(2020, 1, 10),
            split=split,
        )


def test_compute_degradation_flags_overfitting() -> None:
    is_summary = ExperimentSummaryRecord(
        experiment_id=ExperimentId("exp_test"),
        sample_period=SamplePeriod.IN_SAMPLE,
        securities_requested=1,
        securities_completed=1,
        securities_skipped=0,
        mean_stock_return=Decimal("0.20"),
        number_of_trades=10,
        win_rate=Decimal("0.60"),
    )
    oos_summary = ExperimentSummaryRecord(
        experiment_id=ExperimentId("exp_test"),
        sample_period=SamplePeriod.OUT_OF_SAMPLE,
        securities_requested=1,
        securities_completed=1,
        securities_skipped=0,
        mean_stock_return=Decimal("0.05"),
        number_of_trades=3,
        win_rate=Decimal("0.33"),
    )

    degradation = compute_degradation_metrics(is_summary, oos_summary)

    assert degradation.is_to_oos_mean_return_delta == Decimal("-0.15")
    assert degradation.overfitting_warning is True


def test_last_completed_calendar_year_end() -> None:
    assert last_completed_calendar_year_end(as_of=date(2026, 5, 25)) == date(2025, 12, 31)
