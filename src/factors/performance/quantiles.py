"""Quantile portfolio construction for factor performance."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal

from core.types import SecurityId, SignalId
from factors.performance.config import FactorPerformanceConfig
from schemas.factors import FactorScore
from schemas.performance import LongShortResult, QuantileReturnResult, SpreadResult


def effective_quantile_count(security_count: int, quantile_count: int) -> int:
    if security_count < 2:
        raise ValueError("At least two securities are required for quantile analysis")
    return min(quantile_count, security_count)


def assign_quantiles(
    scores: Sequence[FactorScore],
    quantile_count: int,
) -> dict[SecurityId, int]:
    """Assign 1-indexed quantiles where 1 is lowest score and Q is highest."""
    if not scores:
        raise ValueError("At least one factor score is required")

    ordered = sorted(scores, key=lambda row: (row.factor_score, str(row.security_id)))
    bucket_count = effective_quantile_count(len(ordered), quantile_count)
    assignments: dict[SecurityId, int] = {}
    for index, row in enumerate(ordered):
        quantile = (index * bucket_count) // len(ordered) + 1
        assignments[row.security_id] = min(quantile, bucket_count)
    return assignments


def compute_quantile_returns(
    *,
    evaluation_date: date,
    signal_id: SignalId,
    horizon: int,
    scores: Sequence[FactorScore],
    forward_returns: Mapping[SecurityId, Decimal],
    config: FactorPerformanceConfig,
) -> list[QuantileReturnResult]:
    assignments = assign_quantiles(scores, config.quantile_count)
    bucket_count = effective_quantile_count(len(scores), config.quantile_count)
    totals: dict[int, list[Decimal]] = defaultdict(list)

    for row in scores:
        forward_return = forward_returns.get(row.security_id)
        if forward_return is None:
            continue
        totals[assignments[row.security_id]].append(forward_return)

    results: list[QuantileReturnResult] = []
    for quantile in range(1, bucket_count + 1):
        values = totals.get(quantile, [])
        if not values:
            continue
        average_return = sum(values, start=Decimal("0")) / Decimal(len(values))
        results.append(
            QuantileReturnResult(
                evaluation_date=evaluation_date,
                signal_id=signal_id,
                horizon=horizon,
                quantile=quantile,
                security_count=len(values),
                average_return=average_return,
            )
        )
    return results


def compute_spread_and_long_short(
    quantile_returns: Sequence[QuantileReturnResult],
    *,
    config: FactorPerformanceConfig,
) -> tuple[SpreadResult | None, LongShortResult | None]:
    if not quantile_returns:
        return None, None

    by_quantile = {row.quantile: row for row in quantile_returns}
    bucket_count = max(by_quantile)
    top_quantile = config.resolved_top_quantile(bucket_count)
    bottom_quantile = config.resolved_bottom_quantile(bucket_count)
    top_row = by_quantile.get(top_quantile)
    bottom_row = by_quantile.get(bottom_quantile)
    if top_row is None or bottom_row is None:
        return None, None

    spread_return = top_row.average_return - bottom_row.average_return
    reference = quantile_returns[0]
    spread = SpreadResult(
        evaluation_date=reference.evaluation_date,
        signal_id=reference.signal_id,
        horizon=reference.horizon,
        top_quantile=top_quantile,
        bottom_quantile=bottom_quantile,
        spread_return=spread_return,
    )
    long_short = LongShortResult(
        evaluation_date=reference.evaluation_date,
        signal_id=reference.signal_id,
        horizon=reference.horizon,
        long_return=top_row.average_return,
        short_return=bottom_row.average_return,
        long_short_return=spread_return,
    )
    return spread, long_short
