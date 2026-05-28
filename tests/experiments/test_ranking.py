"""Tests for factor ranking."""

from decimal import Decimal

from experiments.enums import SegmentRegime, SegmentTertile
from experiments.ranking import FactorVariantRef, rank_factors_in_segment
from experiments.scoring.weights import DEFAULT_ENTRY_METRIC_WEIGHTS, ENTRY_HIGHER_IS_BETTER
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
    for index, forward_return in enumerate(("0.01", "0.02", "0.03", "0.04", "0.20")):
        candidates.append(
            (
                FactorVariantRef(signal_id="momentum_12_1", variant_id=f"v{index}"),
                {
                    "forward_return": Decimal(forward_return),
                    "information_coefficient": Decimal(forward_return),
                    "hit_rate": Decimal("0.6"),
                    "sharpe_ratio": Decimal(forward_return),
                    "maximum_drawdown": Decimal("-0.05"),
                    "turnover_efficiency": Decimal(forward_return),
                    "robustness_score": Decimal("0.8"),
                },
                None,
            )
        )

    threshold, ranked = rank_factors_in_segment(
        candidates,
        segment,
        qualifying_percentile=95,
        metric_weights=DEFAULT_ENTRY_METRIC_WEIGHTS,
        higher_is_better=ENTRY_HIGHER_IS_BETTER,
    )
    qualified = [row for row in ranked if row.qualified]
    assert threshold >= Decimal("0")
    assert len(qualified) >= 1
    assert sum(row.selection_weight for row in qualified) == Decimal("1")
