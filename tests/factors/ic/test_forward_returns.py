"""Forward return calculator tests."""

from datetime import date
from decimal import Decimal

from core.types import SecurityId
from factors.ic.forward_returns import ForwardReturnCalculator, build_trading_calendar
from schemas.data import PriceBar


class _PriceDataAccess:
    def __init__(self, prices: dict[str, list[PriceBar]]) -> None:
        self._prices = prices

    @property
    def data_version(self):
        from core.types import DataVersion

        return DataVersion("test")

    def get_prices(self, security_id, start_date, end_date, as_of_date):
        del as_of_date
        return [
            bar
            for bar in self._prices[str(security_id)]
            if start_date <= bar.trade_date <= end_date
        ]

    def get_fundamentals(self, security_id, as_of_date):
        del security_id, as_of_date
        return []

    def get_corporate_actions(self, security_id, as_of_date):
        del security_id, as_of_date
        return []

    def get_metadata(self, security_id, as_of_date):
        del security_id, as_of_date
        return None

    def get_delisting_info(self, security_id):
        del security_id
        return None

    def list_security_ids(self):
        return [SecurityId(key) for key in self._prices]


def _bar(trade_date: date, close: str) -> PriceBar:
    price = Decimal(close)
    return PriceBar(
        trade_date=trade_date,
        open=price,
        high=price,
        low=price,
        close=price,
        adjusted_close=price,
        volume=1_000,
    )


def test_forward_return_uses_execution_date_and_adjusted_prices() -> None:
    trading_days = [
        date(2020, 1, 31),
        date(2020, 2, 3),
        date(2020, 2, 4),
        date(2020, 2, 5),
        date(2020, 2, 6),
    ]
    data_access = _PriceDataAccess(
        {
            "100": [
                _bar(date(2020, 1, 31), "100"),
                _bar(date(2020, 2, 3), "100"),
                _bar(date(2020, 2, 4), "110"),
                _bar(date(2020, 2, 5), "115"),
                _bar(date(2020, 2, 6), "120"),
            ]
        }
    )
    calculator = ForwardReturnCalculator()

    results = calculator.calculate_for_universe(
        security_ids=[SecurityId("100")],
        evaluation_date=date(2020, 1, 31),
        horizon=3,
        trading_days=trading_days,
        data_access=data_access,
    )

    assert len(results) == 1
    assert results[0].forward_return == Decimal("0.2")


def test_build_trading_calendar_collects_unique_dates() -> None:
    data_access = _PriceDataAccess(
        {
            "100": [_bar(date(2020, 1, 31), "100"), _bar(date(2020, 2, 3), "101")],
            "200": [_bar(date(2020, 2, 3), "50"), _bar(date(2020, 2, 4), "51")],
        }
    )

    calendar = build_trading_calendar(
        data_access,
        [SecurityId("100"), SecurityId("200")],
        start_date=date(2020, 1, 1),
        end_date=date(2020, 3, 1),
        as_of_date=date(2020, 3, 1),
    )

    assert calendar == [date(2020, 1, 31), date(2020, 2, 3), date(2020, 2, 4)]
