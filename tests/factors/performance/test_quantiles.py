"""Quantile construction tests."""

from datetime import date
from decimal import Decimal

from core.types import SecurityId, SignalId, Ticker
from factors.performance.config import FactorPerformanceConfig
from factors.performance.quantiles import (
    assign_quantiles,
    compute_quantile_returns,
    compute_spread_and_long_short,
)
from schemas.factors import FactorScore
from schemas.ic import ForwardReturn


def test_assign_quantiles_orders_lowest_to_highest() -> None:
    evaluation_date = date(2020, 1, 2)
    scores = [
        FactorScore(
            evaluation_date=evaluation_date,
            security_id=SecurityId("SEC_LOW"),
            ticker=Ticker("LOW"),
            signal_id=SignalId("test"),
            factor_score=Decimal("0.1"),
        ),
        FactorScore(
            evaluation_date=evaluation_date,
            security_id=SecurityId("SEC_HIGH"),
            ticker=Ticker("HIGH"),
            signal_id=SignalId("test"),
            factor_score=Decimal("0.9"),
        ),
        FactorScore(
            evaluation_date=evaluation_date,
            security_id=SecurityId("SEC_MID"),
            ticker=Ticker("MID"),
            signal_id=SignalId("test"),
            factor_score=Decimal("0.5"),
        ),
    ]

    assignments = assign_quantiles(scores, quantile_count=3)

    assert assignments[SecurityId("SEC_LOW")] == 1
    assert assignments[SecurityId("SEC_MID")] == 2
    assert assignments[SecurityId("SEC_HIGH")] == 3


def test_compute_spread_uses_top_minus_bottom(
    sample_scores: list[FactorScore],
    sample_forward_returns: list[ForwardReturn],
    evaluation_date: date,
) -> None:
    config = FactorPerformanceConfig(quantile_count=5, top_quantile=5, bottom_quantile=1)
    horizon_returns = {
        row.security_id: row.forward_return for row in sample_forward_returns
    }
    quantile_returns = compute_quantile_returns(
        evaluation_date=evaluation_date,
        signal_id=SignalId("momentum_12_1"),
        horizon=63,
        scores=sample_scores,
        forward_returns=horizon_returns,
        config=config,
    )
    spread, long_short = compute_spread_and_long_short(quantile_returns, config=config)

    assert spread is not None
    assert long_short is not None
    assert spread.spread_return == long_short.long_short_return
    assert spread.spread_return > Decimal("0")
