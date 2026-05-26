"""Tests for factor ranking."""

from decimal import Decimal

from experiments.enums import SegmentRegime, SegmentTertile
from experiments.metrics import PerformanceMetrics
from experiments.ranking import FactorVariantRef, rank_factors_in_segment
from experiments.segments import SegmentLabels


def test_rank_factors_uses_percentile_threshold() -> None:
    segment = SegmentLabels(
        regime=SegmentRegime.BULL,
        market_cap=SegmentTertile.HIGH,
        volume=SegmentTertile.HIGH,
        volatility=SegmentTertile.MEDIUM,
        liquidity=SegmentTertile.HIGH,
    )
    candidates = []
    for index, cagr in enumerate(("0.01", "0.02", "0.03", "0.04", "0.20")):
        candidates.append(
            (
                FactorVariantRef(signal_id="momentum_12_1", variant_id=f"v{index}"),
                PerformanceMetrics(
                    total_return=Decimal(cagr),
                    cagr=Decimal(cagr),
                    sharpe_ratio=Decimal(cagr),
                    max_drawdown=Decimal("-0.05"),
                    round_trips=10,
                    trading_days=252,
                    calendar_months=Decimal("12"),
                    trades_per_trading_days=Decimal("0.04"),
                    trades_per_month=Decimal("0.83"),
                    trades_per_trading_year=Decimal("10"),
                ),
                Decimal("0.8"),
            )
        )

    threshold, ranked = rank_factors_in_segment(candidates, segment, qualifying_percentile=95)
    qualified = [row for row in ranked if row.qualified]
    assert threshold >= Decimal("0")
    assert len(qualified) >= 1
    assert sum(row.selection_weight for row in qualified) == Decimal("1")
