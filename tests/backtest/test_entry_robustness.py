"""Partial entry robustness builder tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from backtest.entry_robustness import compute_partial_entry_robustness, resolve_ic_summary
from core.types import SecurityId, SignalId, Ticker
from factors.ic.sample_analysis import analyze_ic_by_sample
from research.sample_split import compute_sample_split
from schemas.factors import FactorScore
from schemas.ic import DailyICResult, ForwardReturn, ICSummary


def _daily_ic(
    *,
    evaluation_date: date,
    ic: Decimal,
) -> DailyICResult:
    return DailyICResult(
        evaluation_date=evaluation_date,
        signal_id=SignalId("momentum_12_1"),
        horizon=21,
        security_count=7,
        ic=ic,
    )


def test_resolve_ic_summary_prefers_full_analysis_summary() -> None:
    daily = [
        _daily_ic(evaluation_date=date(2020, 1, 31), ic=Decimal("0.10")),
        _daily_ic(evaluation_date=date(2020, 2, 29), ic=Decimal("0.08")),
        _daily_ic(evaluation_date=date(2020, 8, 31), ic=Decimal("0.02")),
        _daily_ic(evaluation_date=date(2020, 9, 30), ic=Decimal("0.01")),
    ]
    trading_days = sorted({row.evaluation_date for row in daily})
    split = compute_sample_split(
        trading_days,
        calendar_start=date(2020, 1, 31),
        calendar_end=date(2020, 9, 30),
    )
    analysis = analyze_ic_by_sample(
        daily,
        split=split,
        signal_id=SignalId("momentum_12_1"),
        horizon=21,
    )

    summary = resolve_ic_summary(ic_analysis=analysis, full_ic_summary=None)

    assert summary is not None
    assert summary.observation_count == analysis.full_summary.observation_count


def test_compute_partial_entry_robustness_scores_available_dimensions() -> None:
    evaluation_dates = [date(2020, 1, 31), date(2020, 2, 29), date(2020, 8, 31), date(2020, 9, 30)]
    daily = [
        _daily_ic(evaluation_date=evaluation_date, ic=Decimal("0.08"))
        for evaluation_date in evaluation_dates
    ]
    forward_returns = [
        ForwardReturn(
            evaluation_date=evaluation_date,
            security_id=SecurityId("SEC_AAPL"),
            horizon=21,
            forward_return=Decimal("0.03"),
        )
        for evaluation_date in evaluation_dates
    ]
    split = compute_sample_split(
        evaluation_dates,
        calendar_start=evaluation_dates[0],
        calendar_end=evaluation_dates[-1],
    )
    ic_summary = ICSummary(
        signal_id=SignalId("momentum_12_1"),
        horizon=21,
        mean_ic=Decimal("0.08"),
        median_ic=Decimal("0.08"),
        std_ic=Decimal("0.01"),
        ic_information_ratio=Decimal("8"),
        hit_rate=Decimal("1"),
        t_statistic=None,
        p_value=None,
        observation_count=4,
    )

    result, pending = compute_partial_entry_robustness(
        signal_id=SignalId("momentum_12_1"),
        horizon=21,
        ic_summary=ic_summary,
        daily_ic_results=daily,
        forward_returns=forward_returns,
        split=split,
        ic_analysis=None,
    )

    assert result is not None
    assert pending == [
        "market_regime_consistency",
        "data_perturbation_resilience",
        "parameter_sensitivity",
    ]
    assert Decimal("0") <= result.overall_robustness_score <= Decimal("1")
    assert result.market_regime_consistency_score == Decimal("0")
    assert result.ic_stability_score > Decimal("0")


def test_compute_partial_entry_robustness_uses_factor_scores_without_rank_dimension() -> None:
    evaluation_dates = [date(2020, 1, 31), date(2020, 2, 29), date(2020, 8, 31), date(2020, 9, 30)]
    daily = [
        _daily_ic(evaluation_date=evaluation_date, ic=Decimal("0.08"))
        for evaluation_date in evaluation_dates
    ]
    forward_returns = [
        ForwardReturn(
            evaluation_date=evaluation_date,
            security_id=SecurityId("SEC_AAPL"),
            horizon=21,
            forward_return=Decimal("0.03"),
        )
        for evaluation_date in evaluation_dates
    ]
    factor_scores = [
        FactorScore(
            evaluation_date=evaluation_date,
            security_id=SecurityId(f"SEC_{index}"),
            ticker=Ticker(f"T{index}"),
            signal_id=SignalId("momentum_12_1"),
            factor_score=Decimal(index) / Decimal("6"),
        )
        for evaluation_date in evaluation_dates
        for index in range(7)
    ]
    split = compute_sample_split(
        evaluation_dates,
        calendar_start=evaluation_dates[0],
        calendar_end=evaluation_dates[-1],
    )
    ic_summary = ICSummary(
        signal_id=SignalId("momentum_12_1"),
        horizon=21,
        mean_ic=Decimal("0.08"),
        median_ic=Decimal("0.08"),
        std_ic=Decimal("0.01"),
        ic_information_ratio=Decimal("8"),
        hit_rate=Decimal("1"),
        t_statistic=None,
        p_value=None,
        observation_count=4,
    )

    result, pending = compute_partial_entry_robustness(
        signal_id=SignalId("momentum_12_1"),
        horizon=21,
        ic_summary=ic_summary,
        daily_ic_results=daily,
        forward_returns=forward_returns,
        split=split,
        factor_scores=factor_scores,
        ic_analysis=None,
    )

    assert result is not None
    assert "market_regime_consistency" in pending
    assert "data_perturbation_resilience" in pending
    assert result.walk_forward_stability_score >= Decimal("0")
