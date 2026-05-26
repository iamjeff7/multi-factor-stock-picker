"""WeightedMeanFactorCombiner integration tests."""

from datetime import date
from decimal import Decimal

import pytest
from tests.factors.combination.conftest import make_factor_score, make_multi_factor_scores

from core.exceptions import ValidationError
from factors.combination.combiner import WeightedMeanFactorCombiner
from factors.combination.config import FactorCombinationConfig
from factors.combination.enums import MissingFactorPolicy, WeightingMethod


def _default_config(**overrides: object) -> FactorCombinationConfig:
    base = {
        "factor_weights": {
            "momentum_12m": Decimal("1"),
            "quality_roe": Decimal("1"),
            "value_pe": Decimal("1"),
        }
    }
    base.update(overrides)
    return FactorCombinationConfig(**base)


def test_equal_weight_spec_example() -> None:
    combiner = WeightedMeanFactorCombiner(config=_default_config())
    factor_scores = make_multi_factor_scores(
        {
            "AAPL": {
                "momentum_12m": Decimal("0.90"),
                "quality_roe": Decimal("0.70"),
                "value_pe": Decimal("0.50"),
            }
        }
    )

    results = combiner.combine(factor_scores, date(2020, 1, 31))
    assert len(results) == 1
    assert results[0].composite_score == Decimal("0.70")
    assert sum(results[0].factor_contributions_json.values()) == Decimal("0.70")


def test_equal_weight_three_security_example() -> None:
    combiner = WeightedMeanFactorCombiner(config=_default_config())
    factor_scores = make_multi_factor_scores(
        {
            "AAA": {
                "momentum_12m": Decimal("0.80"),
                "quality_roe": Decimal("0.60"),
                "value_pe": Decimal("0.40"),
            }
        }
    )

    results = combiner.combine(factor_scores, date(2020, 1, 31))
    assert results[0].composite_score == Decimal("0.60")


def test_custom_weights_normalize_and_combine() -> None:
    config = FactorCombinationConfig(
        weighting_method=WeightingMethod.CUSTOM_WEIGHT,
        factor_weights={
            "momentum_12m": Decimal("2"),
            "quality_roe": Decimal("3"),
            "value_pe": Decimal("5"),
        },
    )
    combiner = WeightedMeanFactorCombiner(config=config)
    factor_scores = make_multi_factor_scores(
        {
            "AAPL": {
                "momentum_12m": Decimal("1"),
                "quality_roe": Decimal("1"),
                "value_pe": Decimal("1"),
            }
        }
    )

    results = combiner.combine(factor_scores, date(2020, 1, 31))
    assert results[0].composite_score == Decimal("1")


def test_custom_weighted_composite() -> None:
    config = FactorCombinationConfig(
        weighting_method=WeightingMethod.CUSTOM_WEIGHT,
        factor_weights={
            "momentum_12m": Decimal("0.50"),
            "quality_roe": Decimal("0.30"),
            "value_pe": Decimal("0.20"),
        },
    )
    combiner = WeightedMeanFactorCombiner(config=config)
    factor_scores = make_multi_factor_scores(
        {
            "AAPL": {
                "momentum_12m": Decimal("0.90"),
                "quality_roe": Decimal("0.70"),
                "value_pe": Decimal("0.50"),
            }
        }
    )

    results = combiner.combine(factor_scores, date(2020, 1, 31))
    assert results[0].composite_score == Decimal("0.76")


def test_composite_ranking() -> None:
    combiner = WeightedMeanFactorCombiner(config=_default_config())
    factor_scores = make_multi_factor_scores(
        {
            "AAPL": {
                "momentum_12m": Decimal("0.90"),
                "quality_roe": Decimal("0.90"),
                "value_pe": Decimal("0.90"),
            },
            "MSFT": {
                "momentum_12m": Decimal("0.70"),
                "quality_roe": Decimal("0.70"),
                "value_pe": Decimal("0.70"),
            },
            "NVDA": {
                "momentum_12m": Decimal("0.50"),
                "quality_roe": Decimal("0.50"),
                "value_pe": Decimal("0.50"),
            },
        }
    )

    results = combiner.combine(factor_scores, date(2020, 1, 31))
    by_ticker = {row.ticker: row for row in results}

    assert by_ticker["AAPL"].composite_rank == Decimal("1")
    assert by_ticker["MSFT"].composite_rank == Decimal("2")
    assert by_ticker["NVDA"].composite_rank == Decimal("3")


def test_ignore_missing_factor_renormalizes_weights() -> None:
    config = FactorCombinationConfig(
        factor_weights={
            "momentum_12m": Decimal("1"),
            "quality_roe": Decimal("1"),
            "value_pe": Decimal("1"),
        },
        missing_factor_policy=MissingFactorPolicy.IGNORE_MISSING_FACTOR,
        minimum_factor_coverage_pct=Decimal("0.50"),
    )
    combiner = WeightedMeanFactorCombiner(config=config)
    factor_scores = make_multi_factor_scores(
        {
            "AAPL": {
                "momentum_12m": Decimal("0.80"),
                "quality_roe": Decimal("0.60"),
            }
        }
    )

    results = combiner.combine(factor_scores, date(2020, 1, 31))
    assert len(results) == 1
    assert results[0].composite_score == Decimal("0.70")


def test_exclude_security_when_factor_missing() -> None:
    config = FactorCombinationConfig(
        factor_weights={
            "momentum_12m": Decimal("1"),
            "quality_roe": Decimal("1"),
            "value_pe": Decimal("1"),
        },
        missing_factor_policy=MissingFactorPolicy.EXCLUDE_SECURITY,
    )
    combiner = WeightedMeanFactorCombiner(config=config)
    factor_scores = make_multi_factor_scores(
        {
            "AAPL": {
                "momentum_12m": Decimal("0.80"),
                "quality_roe": Decimal("0.60"),
            }
        }
    )

    results = combiner.combine(factor_scores, date(2020, 1, 31))
    assert results == []


def test_assign_neutral_score_for_missing_factor() -> None:
    config = FactorCombinationConfig(
        factor_weights={
            "momentum_12m": Decimal("1"),
            "quality_roe": Decimal("1"),
            "value_pe": Decimal("1"),
        },
        missing_factor_policy=MissingFactorPolicy.ASSIGN_NEUTRAL_SCORE,
    )
    combiner = WeightedMeanFactorCombiner(config=config)
    factor_scores = make_multi_factor_scores(
        {
            "AAPL": {
                "momentum_12m": Decimal("0.80"),
                "quality_roe": Decimal("0.80"),
            }
        }
    )

    results = combiner.combine(factor_scores, date(2020, 1, 31))
    assert results[0].composite_score == Decimal("0.70")


def test_insufficient_factor_coverage_excludes_security() -> None:
    config = FactorCombinationConfig(
        factor_weights={
            "momentum_12m": Decimal("1"),
            "quality_roe": Decimal("1"),
            "value_pe": Decimal("1"),
        },
        missing_factor_policy=MissingFactorPolicy.IGNORE_MISSING_FACTOR,
        minimum_factor_coverage_pct=Decimal("0.50"),
    )
    combiner = WeightedMeanFactorCombiner(config=config)
    factor_scores = make_multi_factor_scores(
        {
            "AAPL": {
                "momentum_12m": Decimal("0.80"),
            }
        }
    )

    results = combiner.combine(factor_scores, date(2020, 1, 31))
    assert results == []


def test_out_of_range_factor_score_halts_execution() -> None:
    combiner = WeightedMeanFactorCombiner(config=_default_config())
    factor_scores = [
        make_factor_score(
            security_id="AAPL",
            ticker="AAPL",
            signal_id="momentum_12m",
            factor_score=Decimal("1.5"),
        )
    ]

    with pytest.raises(ValidationError, match="outside"):
        combiner.combine(factor_scores, date(2020, 1, 31))


def test_factor_contributions_are_traceable() -> None:
    combiner = WeightedMeanFactorCombiner(config=_default_config())
    factor_scores = make_multi_factor_scores(
        {
            "AAPL": {
                "momentum_12m": Decimal("0.90"),
                "quality_roe": Decimal("0.60"),
                "value_pe": Decimal("0.30"),
            }
        }
    )

    results = combiner.combine(factor_scores, date(2020, 1, 31))
    contributions = results[0].factor_contributions_json

    assert set(contributions) == {"momentum_12m", "quality_roe", "value_pe"}
    assert contributions["momentum_12m"] == Decimal("0.30")
    assert contributions["quality_roe"] == Decimal("0.20")
    assert contributions["value_pe"] == Decimal("0.10")
