"""Spearman rank correlation."""

from __future__ import annotations

from decimal import Decimal


def spearman_correlation(left: list[Decimal], right: list[Decimal]) -> Decimal:
    """Compute Spearman rank correlation between two equal-length series."""
    if len(left) != len(right):
        raise ValueError("Series lengths must match")
    if len(left) < 2:
        raise ValueError("At least two observations are required")

    left_ranks = _average_ranks(left)
    right_ranks = _average_ranks(right)
    return _pearson_correlation(left_ranks, right_ranks)


def _average_ranks(values: list[Decimal]) -> list[Decimal]:
    indexed = sorted(enumerate(values), key=lambda item: (item[1], item[0]))
    ranks = [Decimal("0")] * len(values)
    index = 0
    while index < len(indexed):
        tie_end = index
        while (
            tie_end + 1 < len(indexed)
            and indexed[tie_end + 1][1] == indexed[index][1]
        ):
            tie_end += 1

        start_rank = Decimal(index + 1)
        end_rank = Decimal(tie_end + 1)
        average_rank = (start_rank + end_rank) / Decimal("2")
        for position in range(index, tie_end + 1):
            original_index = indexed[position][0]
            ranks[original_index] = average_rank
        index = tie_end + 1
    return ranks


def _pearson_correlation(left: list[Decimal], right: list[Decimal]) -> Decimal:
    count = Decimal(len(left))
    left_mean = sum(left, start=Decimal("0")) / count
    right_mean = sum(right, start=Decimal("0")) / count

    covariance = Decimal("0")
    left_variance = Decimal("0")
    right_variance = Decimal("0")
    for left_value, right_value in zip(left, right, strict=True):
        left_delta = left_value - left_mean
        right_delta = right_value - right_mean
        covariance += left_delta * right_delta
        left_variance += left_delta * left_delta
        right_variance += right_delta * right_delta

    if left_variance == Decimal("0") or right_variance == Decimal("0"):
        raise ValueError("Cannot compute correlation with zero variance")

    denominator = (left_variance * right_variance).sqrt()
    return covariance / denominator
