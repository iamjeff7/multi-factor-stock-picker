"""Spearman correlation tests."""

from decimal import Decimal

import pytest

from factors.ic.spearman import spearman_correlation


def test_spec_example_perfect_positive_correlation() -> None:
    scores = [Decimal("0.90"), Decimal("0.70"), Decimal("0.50")]
    returns = [Decimal("0.12"), Decimal("0.08"), Decimal("0.02")]

    ic = spearman_correlation(scores, returns)
    assert ic == Decimal("1")


def test_perfect_negative_correlation() -> None:
    scores = [Decimal("0.90"), Decimal("0.70"), Decimal("0.50")]
    returns = [Decimal("0.02"), Decimal("0.08"), Decimal("0.12")]

    ic = spearman_correlation(scores, returns)
    assert ic == Decimal("-1")


def test_ties_preserve_monotonic_correlation() -> None:
    scores = [Decimal("0.80"), Decimal("0.80"), Decimal("0.20")]
    returns = [Decimal("0.25"), Decimal("0.25"), Decimal("0.10")]

    ic = spearman_correlation(scores, returns)
    assert ic == Decimal("1")


def test_requires_at_least_two_observations() -> None:
    with pytest.raises(ValueError, match="At least two observations"):
        spearman_correlation([Decimal("0.5")], [Decimal("0.1")])
