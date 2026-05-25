"""Deterministic normalization helpers for robustness scoring."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

SCORE_QUANTIZE = Decimal("0.0000000001")


def quantize_score(value: Decimal) -> Decimal:
    return value.quantize(SCORE_QUANTIZE, rounding=ROUND_HALF_UP)


def clamp(value: Decimal, lower: Decimal, upper: Decimal) -> Decimal:
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value


def normalize_linear(
    value: Decimal,
    *,
    floor: Decimal,
    ceiling: Decimal,
) -> Decimal:
    if ceiling == floor:
        return Decimal("0")
    return clamp((value - floor) / (ceiling - floor), Decimal("0"), Decimal("1"))


def average(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")
    return sum(values, start=Decimal("0")) / Decimal(len(values))


def sample_std(values: list[Decimal]) -> Decimal | None:
    if len(values) < 2:
        return None
    mean_value = average(values)
    variance = sum((value - mean_value) ** 2 for value in values) / Decimal(len(values) - 1)
    return variance.sqrt()


def dispersion_penalty(values: list[Decimal], *, ceiling: Decimal) -> Decimal:
    if len(values) < 2:
        return Decimal("1")
    std_value = sample_std(values)
    if std_value is None:
        return Decimal("1")
    return Decimal("1") - clamp(std_value / ceiling, Decimal("0"), Decimal("1"))


def normalized_spread(values: list[Decimal]) -> Decimal:
    if len(values) < 2:
        return Decimal("0")
    minimum = min(values)
    maximum = max(values)
    scale = maximum - minimum
    if scale == Decimal("0"):
        return Decimal("0")
    return clamp(scale / (abs(maximum) + abs(minimum) + Decimal("1")), Decimal("0"), Decimal("1"))
