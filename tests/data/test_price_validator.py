"""Price validation tests."""

from datetime import date
from decimal import Decimal

from data.validation.price import validate_prices
from schemas.data import PriceBar


def test_invalid_ohlc_detected() -> None:
    bars = [
        PriceBar(
            trade_date=date(2023, 1, 3),
            open=Decimal("10"),
            high=Decimal("9"),
            low=Decimal("8"),
            close=Decimal("10"),
            adjusted_close=Decimal("10"),
            volume=1000,
        )
    ]
    issues = validate_prices("SEC_TEST", bars)
    assert any(issue.check_name == "invalid_ohlc" for issue in issues)
