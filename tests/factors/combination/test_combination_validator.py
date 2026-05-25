"""Factor combination validator tests."""

from datetime import date
from decimal import Decimal

import pytest

from core.exceptions import ValidationError
from core.types import SecurityId, Ticker
from factors.combination.config import FactorCombinationConfig
from factors.combination.validator import FactorCombinationValidator
from schemas.factors import CompositeScore
from tests.factors.combination.conftest import make_factor_score


def _config() -> FactorCombinationConfig:
    return FactorCombinationConfig(
        factor_weights={
            "momentum_12m": Decimal("1"),
            "quality_roe": Decimal("1"),
        }
    )


def test_duplicate_factor_score_fails_validation() -> None:
    validator = FactorCombinationValidator()
    config = _config()
    rows = [
        make_factor_score(
            security_id="AAPL",
            ticker="AAPL",
            signal_id="momentum_12m",
            factor_score=Decimal("0.5"),
        ),
        make_factor_score(
            security_id="AAPL",
            ticker="AAPL",
            signal_id="momentum_12m",
            factor_score=Decimal("0.6"),
        ),
    ]

    with pytest.raises(ValidationError, match="Duplicate factor score"):
        validator.validate_inputs_or_raise(rows, date(2020, 1, 31), config=config)


def test_output_composite_score_bounds_validation() -> None:
    validator = FactorCombinationValidator()
    config = _config()
    scores = [
        CompositeScore(
            evaluation_date=date(2020, 1, 31),
            security_id=SecurityId("AAPL"),
            ticker=Ticker("AAPL"),
            composite_score=Decimal("1.2"),
            composite_rank=Decimal("1"),
        )
    ]

    with pytest.raises(ValidationError, match="outside"):
        validator.validate_outputs_or_raise(scores, config=config)
