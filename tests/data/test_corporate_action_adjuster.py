"""Corporate action adjuster tests."""

from datetime import date
from decimal import Decimal

from core.types import SecurityId
from data.corporate_actions.adjuster import CorporateActionAdjuster
from schemas.data import CorporateAction, PriceBar


def test_split_adjustment_halves_pre_split_prices() -> None:
    sid = SecurityId("SEC_TEST")
    bars = [
        PriceBar(
            trade_date=date(2023, 1, 1),
            open=Decimal("100"),
            high=Decimal("100"),
            low=Decimal("100"),
            close=Decimal("100"),
            adjusted_close=Decimal("100"),
            volume=1000,
        ),
        PriceBar(
            trade_date=date(2023, 1, 10),
            open=Decimal("50"),
            high=Decimal("50"),
            low=Decimal("50"),
            close=Decimal("50"),
            adjusted_close=Decimal("50"),
            volume=1000,
        ),
    ]
    actions = [
        CorporateAction(
            security_id=sid,
            action_date=date(2023, 1, 5),
            action_type="SPLIT",
            ratio=Decimal("2"),
            amount=None,
        )
    ]
    adjusted = CorporateActionAdjuster().adjust_prices(bars, actions)
    pre = next(bar for bar in adjusted if bar.trade_date == date(2023, 1, 1))
    post = next(bar for bar in adjusted if bar.trade_date == date(2023, 1, 10))
    assert pre.adjusted_close == Decimal("50.0000")
    assert post.adjusted_close == Decimal("50.0000")
