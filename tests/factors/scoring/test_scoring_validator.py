"""Factor scoring validator tests."""

from datetime import date
from decimal import Decimal

import pytest
from tests.factors.scoring.conftest import make_entry_signal_result, make_minimum_cross_section

from core.exceptions import ValidationError
from core.types import SecurityId, SignalId, Ticker
from factors.scoring.config import FactorScoringConfig
from factors.scoring.validator import FactorScoringValidator
from schemas.enums import SignalDirection
from schemas.factors import FactorScore


def test_insufficient_sample_fails_validation() -> None:
    validator = FactorScoringValidator()
    config = FactorScoringConfig(minimum_security_count=30)
    raw_signals = make_minimum_cross_section(29)

    report = validator.validate_inputs(
        raw_signals,
        date(2020, 1, 31),
        direction=SignalDirection.HIGHER_IS_BETTER,
        config=config,
    )

    assert not report.passed
    assert any(issue.check_name == "insufficient_sample" for issue in report.issues)


def test_duplicate_security_fails_validation() -> None:
    validator = FactorScoringValidator()
    config = FactorScoringConfig(minimum_security_count=1)
    raw_signals = [
        make_entry_signal_result(security_id="100", ticker="AAA", raw_value=Decimal("1")),
        make_entry_signal_result(security_id="100", ticker="AAA", raw_value=Decimal("2")),
    ]

    with pytest.raises(ValidationError, match="Duplicate security_id"):
        validator.validate_inputs_or_raise(
            raw_signals,
            date(2020, 1, 31),
            direction=SignalDirection.HIGHER_IS_BETTER,
            config=config,
        )


def test_output_score_bounds_validation() -> None:
    validator = FactorScoringValidator()
    config = FactorScoringConfig(minimum_security_count=1)
    scores = [
        FactorScore(
            evaluation_date=date(2020, 1, 31),
            security_id=SecurityId("100"),
            ticker=Ticker("AAA"),
            signal_id=SignalId("momentum_12m"),
            raw_signal_value=Decimal("1"),
            factor_rank=Decimal("1"),
            factor_score=Decimal("1.5"),
        )
    ]

    with pytest.raises(ValidationError, match="outside"):
        validator.validate_outputs_or_raise(scores, config=config)
