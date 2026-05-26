"""Factor performance calculator tests."""

from datetime import date, timedelta
from decimal import Decimal

from core.types import SecurityId, SignalId, Ticker
from factors.performance.calculator import FactorPerformanceCalculator
from factors.performance.config import FactorPerformanceConfig
from research.sample_split import compute_sample_split
from schemas.factors import FactorScore
from schemas.ic import ForwardReturn


def _build_cross_sectional_inputs(
    *,
    start_date: date,
    date_count: int,
    security_count: int,
    horizon: int,
) -> tuple[list[FactorScore], list[ForwardReturn]]:
    factor_scores: list[FactorScore] = []
    forward_returns: list[ForwardReturn] = []
    for offset in range(date_count):
        evaluation_date = start_date + timedelta(days=offset * 30)
        for index in range(security_count):
            security_id = SecurityId(f"SEC_{index}")
            factor_scores.append(
                FactorScore(
                    evaluation_date=evaluation_date,
                    security_id=security_id,
                    ticker=Ticker(f"T{index}"),
                    signal_id=SignalId("momentum_12_1"),
                    factor_score=Decimal(index) / Decimal(security_count - 1),
                )
            )
            forward_returns.append(
                ForwardReturn(
                    evaluation_date=evaluation_date,
                    security_id=security_id,
                    horizon=horizon,
                    forward_return=Decimal("0.01") * Decimal(index + 1),
                )
            )
    return factor_scores, forward_returns


def test_calculator_produces_positive_spread_summary() -> None:
    start_date = date(2020, 1, 2)
    date_count = 12
    factor_scores, forward_returns = _build_cross_sectional_inputs(
        start_date=start_date,
        date_count=date_count,
        security_count=7,
        horizon=63,
    )
    split = compute_sample_split(
        [start_date + timedelta(days=offset * 30) for offset in range(date_count)],
        calendar_start=start_date,
        calendar_end=start_date + timedelta(days=date_count * 30),
    )

    result = FactorPerformanceCalculator(
        config=FactorPerformanceConfig(quantile_count=5, top_quantile=5, bottom_quantile=1),
    ).analyze(
        factor_scores,
        forward_returns,
        signal_id=SignalId("momentum_12_1"),
        horizon=63,
        split=split,
    )

    assert result is not None
    summary = result.full_summary or result.in_sample_summary
    assert summary.mean_spread > Decimal("0")
    assert summary.spread_win_rate > Decimal("0")
