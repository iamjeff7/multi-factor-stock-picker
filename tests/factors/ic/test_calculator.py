"""SpearmanICCalculator integration tests."""

from datetime import date
from decimal import Decimal

import pytest

from core.exceptions import ValidationError
from core.types import SecurityId, SignalId
from factors.ic.calculator import SpearmanICCalculator
from factors.ic.config import ICConfig
from schemas.ic import DailyICResult
from tests.factors.ic.conftest import make_factor_score, make_forward_return


def _spec_example_scores() -> list:
    return [
        make_factor_score(security_id="AAPL", factor_score=Decimal("0.90")),
        make_factor_score(security_id="MSFT", factor_score=Decimal("0.70")),
        make_factor_score(security_id="NVDA", factor_score=Decimal("0.50")),
    ]


def _spec_example_returns() -> dict[SecurityId, Decimal]:
    return {
        SecurityId("AAPL"): Decimal("0.12"),
        SecurityId("MSFT"): Decimal("0.08"),
        SecurityId("NVDA"): Decimal("0.02"),
    }


def test_daily_ic_matches_spec_example() -> None:
    config = ICConfig(minimum_security_count=3)
    calculator = SpearmanICCalculator(config=config)

    result = calculator.calculate_daily_ic(
        _spec_example_scores(),
        _spec_example_returns(),
        date(2020, 1, 31),
        signal_id=SignalId("momentum_12m"),
        horizon=21,
    )

    assert result.ic == Decimal("1")
    assert result.security_count == 3


def test_missing_factor_score_or_return_is_excluded() -> None:
    config = ICConfig(minimum_security_count=2)
    calculator = SpearmanICCalculator(config=config)
    factor_scores = _spec_example_scores()
    forward_returns = {
        SecurityId("AAPL"): Decimal("0.12"),
        SecurityId("MSFT"): Decimal("0.08"),
    }

    result = calculator.calculate_daily_ic(
        factor_scores,
        forward_returns,
        date(2020, 1, 31),
        signal_id=SignalId("momentum_12m"),
        horizon=21,
    )

    assert result.security_count == 2
    assert result.ic == Decimal("1")


def test_insufficient_sample_halts_execution() -> None:
    calculator = SpearmanICCalculator(config=ICConfig(minimum_security_count=30))
    factor_scores = [
        make_factor_score(security_id=f"{index:03d}", factor_score=Decimal(index) / Decimal("100"))
        for index in range(29)
    ]
    forward_returns = {
        row.security_id: Decimal(index) / Decimal("100")
        for index, row in enumerate(factor_scores)
    }

    with pytest.raises(ValidationError, match="Aligned observation count 29"):
        calculator.calculate_daily_ic(
            factor_scores,
            forward_returns,
            date(2020, 1, 31),
            signal_id=SignalId("momentum_12m"),
            horizon=21,
        )


def test_ic_series_and_summary() -> None:
    config = ICConfig(minimum_security_count=3, horizons=[21])
    calculator = SpearmanICCalculator(config=config)
    factor_scores = _spec_example_scores() + [
        make_factor_score(
            security_id="AAPL",
            factor_score=Decimal("0.90"),
            evaluation_date=date(2020, 2, 29),
        ),
        make_factor_score(
            security_id="MSFT",
            factor_score=Decimal("0.50"),
            evaluation_date=date(2020, 2, 29),
        ),
        make_factor_score(
            security_id="NVDA",
            factor_score=Decimal("0.70"),
            evaluation_date=date(2020, 2, 29),
        ),
    ]
    forward_returns = [
        make_forward_return(security_id="AAPL", forward_return=Decimal("0.12")),
        make_forward_return(security_id="MSFT", forward_return=Decimal("0.08")),
        make_forward_return(security_id="NVDA", forward_return=Decimal("0.02")),
        make_forward_return(
            security_id="AAPL",
            forward_return=Decimal("0.02"),
            evaluation_date=date(2020, 2, 29),
        ),
        make_forward_return(
            security_id="MSFT",
            forward_return=Decimal("0.12"),
            evaluation_date=date(2020, 2, 29),
        ),
        make_forward_return(
            security_id="NVDA",
            forward_return=Decimal("0.08"),
            evaluation_date=date(2020, 2, 29),
        ),
    ]

    daily_results = calculator.calculate_ic_series(
        factor_scores,
        forward_returns,
        signal_id=SignalId("momentum_12m"),
    )
    summary = calculator.summarize(
        daily_results,
        signal_id=SignalId("momentum_12m"),
        horizon=21,
    )

    assert len(daily_results) == 2
    assert daily_results[0].ic == Decimal("1")
    assert daily_results[1].ic == Decimal("-1")
    assert summary.mean_ic == Decimal("0")
    assert summary.hit_rate == Decimal("0.5")
    assert summary.observation_count == 2


def test_summary_requires_observations() -> None:
    calculator = SpearmanICCalculator(config=ICConfig(minimum_security_count=1))
    with pytest.raises(ValueError, match="At least one daily IC observation"):
        calculator.summarize([], signal_id=SignalId("momentum_12m"), horizon=21)
