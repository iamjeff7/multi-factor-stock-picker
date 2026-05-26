"""Forward return aggregate tests."""

from datetime import date
from decimal import Decimal

from tests.factors.ic.conftest import make_forward_return

from factors.ic.aggregates import summarize_forward_returns


def test_summarize_forward_returns() -> None:
    forward_returns = [
        make_forward_return(security_id="AAPL", forward_return=Decimal("0.10")),
        make_forward_return(
            security_id="MSFT",
            forward_return=Decimal("-0.02"),
            evaluation_date=date(2020, 2, 29),
        ),
    ]

    mean_value, positive_ratio = summarize_forward_returns(forward_returns, horizon=21)

    assert mean_value == Decimal("0.04")
    assert positive_ratio == Decimal("0.5")
